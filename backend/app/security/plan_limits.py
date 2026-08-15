"""Free-tier usage caps (domains, scans/month) — the enforcement side of
app.services.billing.effective_tier. Mirrors app/security/rate_limit.py's
shape deliberately: a plain exception raised by a pure, DB-reading function,
caught locally by the one call site that needs to audit-log it before
converting to an HTTPException, with a global handler in main.py as a
safety net for any call site that forgets to.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.domain import Domain
from app.models.enums import PlanTier
from app.models.scan import Scan
from app.models.user import User
from app.services.billing import effective_tier

settings = get_settings()


class PlanLimitExceeded(Exception):
    """Caught locally at each call site that needs to audit-log it, and by
    the global handler in main.py as a safety net for any other."""


async def enforce_domain_limit(db: AsyncSession, *, user: User) -> None:
    if await effective_tier(db, user.id) == PlanTier.PRO:
        return

    count = await db.scalar(select(func.count()).select_from(Domain).where(Domain.user_id == user.id))
    if count is not None and count >= settings.free_tier_domain_limit:
        raise PlanLimitExceeded(
            f"Free plan is limited to {settings.free_tier_domain_limit} domain"
            f"{'s' if settings.free_tier_domain_limit != 1 else ''} — upgrade to Pro for up to 10."
        )


async def enforce_scan_quota(db: AsyncSession, *, user: User) -> None:
    if await effective_tier(db, user.id) == PlanTier.PRO:
        return

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = await db.scalar(
        select(func.count())
        .select_from(Scan)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(Domain.user_id == user.id, Scan.started_at >= month_start)
    )
    if count is not None and count >= settings.free_tier_scans_per_month:
        raise PlanLimitExceeded(
            f"Free plan includes {settings.free_tier_scans_per_month} scans per month — "
            "upgrade to Pro for unlimited scans."
        )
