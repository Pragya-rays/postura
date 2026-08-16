from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import client_ip, get_current_user
from app.models.user import User
from app.schemas.auth import LoginIn, RegisterIn, UserOut
from app.security.jwt import create_access_token
from app.security.passwords import hash_password, verify_password
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Verified against on a login attempt for an email that doesn't exist, so a
# nonexistent-user response takes roughly the same time as a wrong-password
# response — cheap mitigation against user-enumeration-by-timing.
_DUMMY_HASH = hash_password("postura-dummy-password-for-timing-parity")


def _set_session_cookie(response: Response, user_id) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_expire_minutes * 60,
        domain=settings.cookie_domain,
        path="/",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        # Generic message — do not reveal whether the email is already registered.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not create account")

    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()
    await write_audit_log(db, action="auth.register", user_id=user.id, ip_address=client_ip(request))
    await db.commit()

    _set_session_cookie(response, user.id)
    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
async def login(body: LoginIn, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == body.email))

    password_ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok:
        await write_audit_log(
            db, action="auth.login.failure", target=body.email, ip_address=client_ip(request)
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    await write_audit_log(db, action="auth.login.success", user_id=user.id, ip_address=client_ip(request))
    await db.commit()

    _set_session_cookie(response, user.id)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    # samesite/secure must match how the cookie was set, or some browsers
    # won't actually clear it.
    response.delete_cookie(
        key=settings.cookie_name,
        domain=settings.cookie_domain,
        path="/",
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
