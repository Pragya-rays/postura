"""Shared FastAPI dependencies: DB session (app.db.get_db), current-user
resolution from the httpOnly session cookie, and request IP extraction for
audit logging / rate limiting."""
import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.models.user import User
from app.security.jwt import InvalidTokenError, decode_access_token

settings = get_settings()


class AuthError(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise AuthError()
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise AuthError("Session expired or invalid")

    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise AuthError("Session expired or invalid")

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise AuthError("Session expired or invalid")
    return user


def client_ip(request: Request) -> str | None:
    # Trust X-Forwarded-For only if we're actually behind a known proxy; for
    # MVP (single-hop reverse proxy in front of the container) take the first
    # hop, falling back to the direct peer address.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
