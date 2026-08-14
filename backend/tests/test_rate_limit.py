"""Unit tests for enforce_scan_rate_limits against real rows in the test DB
— faster and more direct than driving it through N real HTTP scan starts.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain
from app.models.enums import VerificationStatus
from app.models.scan import Scan
from app.models.user import User
from app.models.enums import ScanStatus, ScanTier
from app.security.passwords import hash_password
from app.security.rate_limit import RateLimitExceeded, enforce_scan_rate_limits, settings


async def _make_user_and_domain(session: AsyncSession, hostname: str) -> tuple[User, Domain]:
    user = User(email=f"ratelimit-{uuid.uuid4().hex[:8]}@example.com", password_hash=hash_password("x"))
    session.add(user)
    await session.flush()

    domain = Domain(
        user_id=user.id,
        hostname=hostname,
        verification_status=VerificationStatus.UNVERIFIED,
        verification_token="postura-verify-test",
        scans=[],
    )
    session.add(domain)
    await session.flush()
    return user, domain


async def _add_scan(session: AsyncSession, domain: Domain) -> None:
    session.add(Scan(domain=domain, status=ScanStatus.COMPLETE, tier=ScanTier.PUBLIC, stages=[]))
    await session.flush()


@pytest.fixture(autouse=True)
def _tight_limits(monkeypatch: pytest.MonkeyPatch):
    """Small thresholds so the test doesn't need to create dozens of rows."""
    monkeypatch.setattr(settings, "rate_limit_scans_per_user_per_window", 2)
    monkeypatch.setattr(settings, "rate_limit_scans_per_target_per_window", 2)


async def _session(_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    return async_sessionmaker(bind=_engine, expire_on_commit=False)()


async def test_under_threshold_does_not_raise(client, _engine) -> None:
    async with await _session(_engine) as session:
        user, domain = await _make_user_and_domain(session, f"rl-under-{uuid.uuid4().hex[:8]}.example")
        await _add_scan(session, domain)
        await session.commit()

        await enforce_scan_rate_limits(session, user_id=user.id, hostname=domain.hostname)  # 1 < 2, should not raise


async def test_per_user_threshold_raises(client, _engine) -> None:
    async with await _session(_engine) as session:
        user, domain = await _make_user_and_domain(session, f"rl-user-{uuid.uuid4().hex[:8]}.example")
        await _add_scan(session, domain)
        await _add_scan(session, domain)  # 2 scans == threshold of 2
        await session.commit()

        with pytest.raises(RateLimitExceeded):
            await enforce_scan_rate_limits(session, user_id=user.id, hostname=domain.hostname)


async def test_per_target_threshold_raises_even_for_different_users(client, _engine) -> None:
    async with await _session(_engine) as session:
        hostname = f"rl-target-{uuid.uuid4().hex[:8]}.example"
        user1, domain1 = await _make_user_and_domain(session, hostname)
        await _add_scan(session, domain1)

        user2 = User(email=f"ratelimit-{uuid.uuid4().hex[:8]}@example.com", password_hash=hash_password("x"))
        session.add(user2)
        await session.flush()
        domain2 = Domain(
            user_id=user2.id,
            hostname=hostname,
            verification_status=VerificationStatus.UNVERIFIED,
            verification_token="postura-verify-test",
            scans=[],
        )
        session.add(domain2)
        await session.flush()
        await _add_scan(session, domain2)
        await session.commit()

        # user2 has only started 1 scan themselves (under the per-user limit),
        # but the TARGET hostname has been scanned twice across both users.
        with pytest.raises(RateLimitExceeded):
            await enforce_scan_rate_limits(session, user_id=user2.id, hostname=hostname)
