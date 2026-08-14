import secrets

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.deps import client_ip, get_current_user
from app.models.domain import Domain
from app.models.enums import VerificationStatus
from app.models.user import User
from app.schemas.domain import DomainIn, DomainOut, DomainVerifyOut
from app.security.ssrf import SSRFError, resolve_and_validate
from app.services.audit import write_audit_log
from app.services.verification import verify_domain_ownership

router = APIRouter(prefix="/domains", tags=["domains"])


def _generate_verification_token() -> str:
    return f"postura-verify-{secrets.token_hex(6)}"


@router.get("", response_model=list[DomainOut])
async def list_domains(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.scalars(
        select(Domain)
        .where(Domain.user_id == user.id)
        .options(selectinload(Domain.scans))
        .order_by(Domain.added_at.desc())
    )
    return [DomainOut.model_validate(d) for d in result.all()]


@router.post("", response_model=DomainOut, status_code=status.HTTP_201_CREATED)
async def add_domain(
    body: DomainIn, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    hostname = body.hostname.strip().lower()

    # Server-side SSRF pre-check — the authoritative one.
    # frontend/lib/validate-target.ts's client-side check is a UX nicety
    # only; reject BEFORE any row is created or any network call is made.
    try:
        await resolve_and_validate(hostname, port=443)
    except SSRFError as exc:
        await write_audit_log(
            db, action="domain.blocked_ssrf", user_id=user.id, target=hostname, ip_address=client_ip(request)
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    existing = await db.scalar(select(Domain).where(Domain.user_id == user.id, Domain.hostname == hostname))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain already added")

    domain = Domain(
        user_id=user.id,
        hostname=hostname,
        verification_status=VerificationStatus.UNVERIFIED,
        verification_token=_generate_verification_token(),
        # Explicitly initializes the collection as "loaded" — without this,
        # accessing `.last_scan` (-> `.scans`) after commit triggers an
        # implicit async lazy-load, which raises MissingGreenlet because
        # Pydantic's serializer reads it outside an awaited context.
        scans=[],
    )
    db.add(domain)
    await db.flush()
    await write_audit_log(db, action="domain.added", user_id=user.id, target=hostname, ip_address=client_ip(request))
    await db.commit()

    return DomainOut.model_validate(domain)


@router.post("/{domain_id}/verify", response_model=DomainVerifyOut)
async def verify_domain(
    domain_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    domain = await db.scalar(select(Domain).where(Domain.id == domain_id, Domain.user_id == user.id))
    if domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    verified = await verify_domain_ownership(domain.hostname, domain.verification_token)
    domain.verification_status = VerificationStatus.VERIFIED if verified else VerificationStatus.PENDING
    await db.commit()

    return DomainVerifyOut(verification_status=domain.verification_status, verified=verified)
