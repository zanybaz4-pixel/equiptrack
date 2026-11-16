from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select

from app.db import DB
from app.lending_schemas import LoginIn, SessionOut
from app.models import AuthSession, User
from app.schemas import errors
from app.security import (
    COOKIE, SESSION_LIFETIME, Current, Writer, csrf_token, hasher,
    login_capacity, require_origin, token_hash, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=SessionOut, responses=errors(400, 401, 403, 422, 429, 500, 503))
def login(body: LoginIn, response: Response, db: DB, origin: Annotated[None, Depends(require_origin)]):
    if not login_capacity.acquire(blocking=False):
        raise HTTPException(429, "Too many login attempts. Retry shortly.", headers={"Retry-After": "1"})
    try:
        user = db.scalar(select(User).where(User.email == body.email).with_for_update())
        if not verify_password(body.password, user.password_hash if user else None) or not user or not user.is_active:
            raise HTTPException(401, "Email or password is incorrect.")
        if hasher.check_needs_rehash(user.password_hash):
            user.password_hash = hasher.hash(body.password)
        now = datetime.now(UTC)
        # Remove expired sessions for this account during successful login.
        db.execute(delete(AuthSession).where(AuthSession.user_id == user.id, AuthSession.expires_at <= now))
        token = token_urlsafe(32)
        db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=now + SESSION_LIFETIME))
        result = SessionOut(user=user, csrf_token=csrf_token(token))
        db.commit()
    finally:
        login_capacity.release()
    response.set_cookie(COOKIE, token, secure=True, httponly=True, samesite="strict",
                        max_age=int(SESSION_LIFETIME.total_seconds()), path="/")
    return result


@router.get("/me", response_model=SessionOut, responses=errors(401, 500, 503))
def me(principal: Current):
    return SessionOut(user=principal.user, csrf_token=csrf_token(principal.token))


@router.post("/logout", responses=errors(401, 403, 500, 503))
def logout(response: Response, db: DB, principal: Writer) -> dict[str, bool]:
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(principal.token)))
    db.commit()
    response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="strict")
    return {"signed_out": True}
