from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.db import DB
from app.lending_schemas import PasswordResetIn, PasswordResetRequestIn
from app.models import AuthSession, PasswordResetLimit, PasswordResetToken, User
from app.recovery_mail import mail_ready, send_password_reset
from app.schemas import errors
from app.security import COOKIE, hasher, login_capacity, require_origin, token_hash
from app.transactions import audit

router = APIRouter(prefix="/api/auth", tags=["authentication"])
RESET_LIFETIME = timedelta(minutes=15)
REQUEST_MESSAGE = {"message": "If an active account uses that email, a password reset link will arrive shortly. Check your spam folder too."}
INVALID_LINK = "This reset link is invalid or has expired. Request a new link."


def delivery_allowed(db, email: str, now: datetime):
    """Atomically apply a one-minute cooldown and five requests per hour across workers."""
    key = token_hash(email)
    table = PasswordResetLimit
    db.execute(delete(table).where(table.last_requested_at < now - timedelta(days=1)))
    statement = insert(table).values(email_hash=key, window_started_at=now,
                                     last_requested_at=now, attempts=1)
    changed = statement.on_conflict_do_update(
        index_elements=[table.email_hash],
        set_={
            "window_started_at": statement.excluded.window_started_at,
            "last_requested_at": statement.excluded.last_requested_at,
            "attempts": 1,
        },
        where=table.window_started_at <= now - timedelta(hours=1),
    ).returning(table.email_hash)
    if db.scalar(changed):
        return True
    limit = db.get(table, key, with_for_update=True)
    if limit.attempts >= 5 or limit.last_requested_at > now - timedelta(minutes=1):
        return False
    limit.attempts += 1
    limit.last_requested_at = now
    return True


@router.post("/forgot-password", status_code=202, responses=errors(400, 403, 422, 429, 500, 503))
def forgot_password(body: PasswordResetRequestIn, tasks: BackgroundTasks, db: DB,
                    origin: Annotated[None, Depends(require_origin)]):
    if not mail_ready():
        raise HTTPException(503, "Password reset email is not available yet. Please contact your custodian.")
    now = datetime.now(UTC)
    allowed = delivery_allowed(db, body.email, now)
    token = token_urlsafe(32)
    user = db.scalar(select(User).where(User.email == body.email, User.is_active.is_(True)))
    db.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at <= now))
    if allowed and user:
        db.add(PasswordResetToken(token_hash=token_hash(token), user_id=user.id,
                                 created_at=now, expires_at=now + RESET_LIFETIME))
    db.commit()
    # Mail latency/failure must not reveal whether the account exists.
    if allowed and user:
        tasks.add_task(send_password_reset, body.email, token)
    return REQUEST_MESSAGE


@router.post("/reset-password", responses=errors(400, 403, 422, 429, 500, 503))
def reset_password(body: PasswordResetIn, response: Response, db: DB,
                   origin: Annotated[None, Depends(require_origin)]):
    if not login_capacity.acquire(blocking=False):
        raise HTTPException(429, "Too many attempts. Retry shortly.", headers={"Retry-After": "1"})
    try:
        hashed_token = token_hash(body.token)
        user_id = db.scalar(select(PasswordResetToken.user_id).where(
            PasswordResetToken.token_hash == hashed_token))
        if user_id is None:
            raise HTTPException(400, INVALID_LINK)
        new_hash = hasher.hash(body.password)
        # Lock the same user as login before reading/consuming the challenge.
        # Concurrent reset and login requests cannot preserve an old session.
        user = db.get(User, user_id, with_for_update=True)
        challenge = db.get(PasswordResetToken, hashed_token)
        if not user or not user.is_active or not challenge or challenge.expires_at <= datetime.now(UTC):
            raise HTTPException(400, INVALID_LINK)
        user.password_hash = new_hash
        db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
        db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
        audit(db, user.id, "auth.password_reset", "user", user.id)
        db.commit()
    finally:
        login_capacity.release()
    response.delete_cookie(COOKIE, path="/", secure=True, httponly=True, samesite="strict")
    return {"message": "Your password has been reset. Sign in with your new password."}
