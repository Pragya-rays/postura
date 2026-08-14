import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import async_session_factory, get_db
from app.deps import client_ip, get_current_user
from app.models.domain import Domain
from app.models.enums import ScanStatus, ScanTier, VerificationStatus
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.user import User
from app.schemas.finding import FindingOut
from app.schemas.report import ScanReportOut
from app.schemas.scan import ScanStageOut, ScanSummaryOut, StartScanIn
from app.security.rate_limit import RateLimitExceeded, enforce_scan_rate_limits
from app.services.audit import write_audit_log
from app.services.scan_orchestrator import initial_stages, run_scan_pipeline
from scanner.enums import SEVERITY_ORDER

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=list[ScanSummaryOut])
async def list_scans(
    domain_id: uuid.UUID | None = Query(default=None, alias="domainId"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Scan)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(Domain.user_id == user.id)
        .options(selectinload(Scan.domain))
        .order_by(Scan.started_at.desc())
    )
    if domain_id is not None:
        stmt = stmt.where(Scan.domain_id == domain_id)
    result = await db.scalars(stmt)
    return [ScanSummaryOut.model_validate(s) for s in result.all()]


@router.post("", response_model=ScanSummaryOut, status_code=status.HTTP_201_CREATED)
async def start_scan(
    body: StartScanIn,
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    domain = await db.scalar(select(Domain).where(Domain.id == body.domain_id, Domain.user_id == user.id))
    if domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    try:
        await enforce_scan_rate_limits(db, user_id=user.id, hostname=domain.hostname)
    except RateLimitExceeded as exc:
        await write_audit_log(
            db, action="scan.rate_limited", user_id=user.id, target=domain.hostname, ip_address=client_ip(request)
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))

    tier = ScanTier.VERIFIED if domain.verification_status == VerificationStatus.VERIFIED else ScanTier.PUBLIC

    # `domain=domain` (not `domain_id=domain.id`) so the relationship is
    # populated immediately in this session, without a reload — the
    # response serializes `scan.hostname` (a property reading `scan.domain`)
    # right after this, before any background work has happened.
    scan = Scan(domain=domain, status=ScanStatus.COLLECTING, tier=tier, stages=initial_stages())
    db.add(scan)
    await db.flush()
    await write_audit_log(
        db, action="scan.started", user_id=user.id, target=domain.hostname, ip_address=client_ip(request)
    )
    await db.commit()

    background_tasks.add_task(run_scan_pipeline, scan.id, async_session_factory)

    return ScanSummaryOut.model_validate(scan)


@router.get("/{scan_id}", response_model=ScanReportOut)
async def get_scan(scan_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    scan = await db.scalar(
        select(Scan)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(Scan.id == scan_id, Domain.user_id == user.id)
        .options(selectinload(Scan.domain))
    )
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    findings_result = await db.scalars(select(Finding).where(Finding.scan_id == scan.id))
    findings = list(findings_result.all())
    severity_rank = {s.value: i for i, s in enumerate(SEVERITY_ORDER)}
    findings.sort(key=lambda f: severity_rank.get(f.severity.value, len(SEVERITY_ORDER)))

    breakdown = {s.value: 0 for s in SEVERITY_ORDER}
    for finding in findings:
        breakdown[finding.severity.value] += 1

    return ScanReportOut(
        scan=ScanSummaryOut.model_validate(scan),
        stages=[ScanStageOut.model_validate(s) for s in scan.stages],
        summary=scan.summary,
        findings=[FindingOut.model_validate(f) for f in findings],
        severity_breakdown=breakdown,
    )
