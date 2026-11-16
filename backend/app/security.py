from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from hashlib import sha256
from hmac import compare_digest, digest
from secrets import token_urlsafe
from threading import BoundedSemaphore
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyCookie
from sqlalchemy import select

from app.config import get_settings
from app.db import DB
from app.models import AuthSession, User

COOKIE = "__Host-equiptrack"
SESSION_LIFETIME = timedelta(hours=8)
cookie_scheme = APIKeyCookie(name=COOKIE, auto_error=False)
hasher = PasswordHasher()
# Bound simultaneous Argon2 jobs (64 MiB each with the chosen defaults).
login_capacity = BoundedSemaphore(4)


@lru_cache(maxsize=1)
def dummy_hash():
    return hasher.hash(token_urlsafe(32))


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return hasher.verify(password_hash or dummy_hash(), password)
    except (InvalidHashError, VerificationError):
        return False


def token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return digest(token.encode(), b"equiptrack-csrf-v1", "sha256").hex()


def require_origin(request: Request):
    if request.headers.get("Origin") != get_settings().app_origin.rstrip("/"):
        raise HTTPException(403, "The request origin is not allowed.")


@dataclass
class Principal:
    user: User
    token: str


def require_session(db: DB, token: Annotated[str | None, Security(cookie_scheme)]):
    if token is None or len(token) != 43:
        raise HTTPException(401, "Sign in to continue.")
    user = db.scalar(
        select(User).join(AuthSession, AuthSession.user_id == User.id)
        .where(AuthSession.token_hash == token_hash(token),
               AuthSession.expires_at > datetime.now(UTC), User.is_active.is_(True))
    )
    if user is None:
        raise HTTPException(401, "Sign in to continue.")
    return Principal(user, token)


Current = Annotated[Principal, Depends(require_session)]


def authorize_write(request: Request, principal: Current):
    require_origin(request)
    header = request.headers.get("X-CSRF-Token", "")
    if len(header) != 64 or not header.isascii() or not compare_digest(header, csrf_token(principal.token)):
        raise HTTPException(403, "The CSRF token is invalid.")
    return principal


Writer = Annotated[Principal, Depends(authorize_write)]


def require_role(principal: Principal, role: str):
    if principal.user.role != role:
        raise HTTPException(403, "Your role cannot perform this action.")


def admin_read(principal: Current):
    require_role(principal, "admin")
    return principal


def admin_write(principal: Writer):
    require_role(principal, "admin")
    return principal


def borrower_write(principal: Writer):
    require_role(principal, "borrower")
    return principal


Admin = Annotated[Principal, Depends(admin_read)]
AdminWriter = Annotated[Principal, Depends(admin_write)]
BorrowerWriter = Annotated[Principal, Depends(borrower_write)]
