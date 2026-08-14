"""JWT issuance/verification for the httpOnly session cookie. Tokens carry
only the user id — never put anything sensitive (email, plan, etc.) in the
payload, since the cookie is the only place this data lives client-side and
we don't want stale claims; every request re-reads the user row from DB."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class TokenPayload(BaseModel):
    sub: str  # user id, as string
    exp: int


class InvalidTokenError(Exception):
    pass


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload.model_validate(raw)
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
