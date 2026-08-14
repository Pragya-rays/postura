"""Per-user and per-target scan rate limiting. DB-backed (queries `scans`
against a rolling time window) rather than in-memory or Redis — correct
across process restarts without needing Redis for the MVP.

Known limitation (documented, not silently ignored): this is a courtesy
limit, not a hard security boundary — with multiple Uvicorn workers, two
concurrent requests on different workers could both pass the count check in
the same window before either commits. Move to Redis (or a DB-level
advisory lock) before running more than one worker process.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.domain import Domain
from app.models.scan import Scan

settings = get_settings()


class RateLimitExceeded(Exception):
    """Caught locally at the one call site that needs to audit-log it, and
    by the global handler in main.py as a safety net for any other."""


async def enforce_scan_rate_limits(db: AsyncSession, *, user_id: uuid.UUID, hostname: str) -> None:
    since = datetime.now(timezone.utc) - timedelta(minutes=settings.rate_limit_window_minutes)

    user_count = await db.scalar(
        select(func.count())
        .select_from(Scan)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(Domain.user_id == user_id, Scan.started_at >= since)
    )
    if user_count is not None and user_count >= settings.rate_limit_scans_per_user_per_window:
        raise RateLimitExceeded(
            f"Too many scans started in the last {settings.rate_limit_window_minutes} minutes — "
            "please wait before starting another."
        )

    target_count = await db.scalar(
        select(func.count())
        .select_from(Scan)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(Domain.hostname == hostname, Scan.started_at >= since)
    )
    if target_count is not None and target_count >= settings.rate_limit_scans_per_target_per_window:
        raise RateLimitExceeded(
            f"This target has already been scanned several times in the last "
            f"{settings.rate_limit_window_minutes} minutes — please wait before scanning it again."
        )
