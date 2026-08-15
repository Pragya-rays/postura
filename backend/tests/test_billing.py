"""Unit tests for plan-limit enforcement and webhook event handling —
testing enforce_domain_limit/enforce_scan_quota/apply_webhook_event directly
against real rows in the test DB, same philosophy as test_rate_limit.py:
faster and more direct than driving everything through real HTTP requests
and real Stripe API calls.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.domain import Domain
from app.models.enums import ScanStatus, ScanTier, SubscriptionStatus, VerificationStatus
from app.models.scan import Scan
from app.models.subscription import Subscription
from app.models.user import User
from app.security.passwords import hash_password
from app.security.plan_limits import PlanLimitExceeded, enforce_domain_limit, enforce_scan_quota
from app.security.plan_limits import settings as plan_limits_settings
from app.services.billing import apply_webhook_event


async def _session(_engine) -> AsyncSession:
    return async_sessionmaker(bind=_engine, expire_on_commit=False)()


async def _make_user(session: AsyncSession) -> User:
    user = User(email=f"billing-{uuid.uuid4().hex[:8]}@example.com", password_hash=hash_password("x"))
    session.add(user)
    await session.flush()
    return user


async def _make_domain(session: AsyncSession, user: User) -> Domain:
    domain = Domain(
        user_id=user.id,
        hostname=f"billing-{uuid.uuid4().hex[:8]}.example",
        verification_status=VerificationStatus.UNVERIFIED,
        verification_token="postura-verify-test",
        scans=[],
    )
    session.add(domain)
    await session.flush()
    return domain


async def _add_scan(session: AsyncSession, domain: Domain) -> None:
    session.add(Scan(domain=domain, status=ScanStatus.COMPLETE, tier=ScanTier.PUBLIC, stages=[]))
    await session.flush()


async def _make_pro_subscription(session: AsyncSession, user: User) -> None:
    session.add(
        Subscription(
            user_id=user.id,
            stripe_customer_id=f"cus_{uuid.uuid4().hex[:14]}",
            stripe_subscription_id=f"sub_{uuid.uuid4().hex[:14]}",
            status=SubscriptionStatus.ACTIVE,
        )
    )
    await session.flush()


@pytest.fixture(autouse=True)
def _tight_limits(monkeypatch: pytest.MonkeyPatch):
    """Small thresholds so tests don't need dozens of rows."""
    monkeypatch.setattr(plan_limits_settings, "free_tier_domain_limit", 1)
    monkeypatch.setattr(plan_limits_settings, "free_tier_scans_per_month", 1)


# --- enforce_domain_limit ---------------------------------------------------


async def test_domain_limit_under_threshold_does_not_raise(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        await session.commit()

        await enforce_domain_limit(session, user=user)  # 0 existing < 1, should not raise


async def test_domain_limit_at_threshold_raises(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        await _make_domain(session, user)
        await session.commit()

        with pytest.raises(PlanLimitExceeded):
            await enforce_domain_limit(session, user=user)


async def test_domain_limit_pro_user_bypasses(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        await _make_domain(session, user)
        await _make_pro_subscription(session, user)
        await session.commit()

        await enforce_domain_limit(session, user=user)  # Pro: unlimited, should not raise


# --- enforce_scan_quota ------------------------------------------------------


async def test_scan_quota_under_threshold_does_not_raise(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        await _make_domain(session, user)
        await session.commit()

        await enforce_scan_quota(session, user=user)  # 0 scans this month < 1, should not raise


async def test_scan_quota_at_threshold_raises(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        domain = await _make_domain(session, user)
        await _add_scan(session, domain)
        await session.commit()

        with pytest.raises(PlanLimitExceeded):
            await enforce_scan_quota(session, user=user)


async def test_scan_quota_pro_user_bypasses(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        domain = await _make_domain(session, user)
        await _add_scan(session, domain)
        await _make_pro_subscription(session, user)
        await session.commit()

        await enforce_scan_quota(session, user=user)  # Pro: unlimited, should not raise


# --- apply_webhook_event -----------------------------------------------------


def _checkout_completed_event(*, event_id: str, user_id: uuid.UUID, customer_id: str, subscription_id: str) -> dict:
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": str(user_id),
                "customer": customer_id,
                "subscription": subscription_id,
            }
        },
    }


def _subscription_updated_event(*, event_id: str, subscription_id: str, customer_id: str, status: str) -> dict:
    return {
        "id": event_id,
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": subscription_id,
                "customer": customer_id,
                "status": status,
                "items": {"data": [{"price": {"id": "price_test"}}]},
                "current_period_end": int(datetime.now(timezone.utc).timestamp()) + 30 * 24 * 3600,
                "cancel_at_period_end": False,
            }
        },
    }


async def test_webhook_subscription_updated_reads_period_end_from_item(client, _engine) -> None:
    """Newer Stripe API versions moved current_period_end from the
    subscription object onto each subscription item (a subscription can now
    have items with different billing periods) — this must still work when
    the top-level field is absent, matching what real Stripe sandboxes send."""
    async with await _session(_engine) as session:
        user = await _make_user(session)
        customer_id = f"cus_{uuid.uuid4().hex[:14]}"
        subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
        session.add(Subscription(user_id=user.id, stripe_customer_id=customer_id, stripe_subscription_id=subscription_id))
        await session.commit()

        item_period_end = int(datetime.now(timezone.utc).timestamp()) + 30 * 24 * 3600
        event = {
            "id": f"evt_{uuid.uuid4().hex[:14]}",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": subscription_id,
                    "customer": customer_id,
                    "status": "active",
                    "items": {"data": [{"price": {"id": "price_test"}, "current_period_end": item_period_end}]},
                    "cancel_at_period_end": True,
                    # No top-level current_period_end — the new API shape.
                }
            },
        }
        await apply_webhook_event(session, event)
        await session.commit()

        subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user.id))
        assert subscription.current_period_end is not None
        assert int(subscription.current_period_end.timestamp()) == item_period_end
        assert subscription.cancel_at_period_end is True


async def test_webhook_checkout_completed_creates_subscription(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        await session.commit()

        customer_id = f"cus_{uuid.uuid4().hex[:14]}"
        subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
        event = _checkout_completed_event(
            event_id=f"evt_{uuid.uuid4().hex[:14]}",
            user_id=user.id,
            customer_id=customer_id,
            subscription_id=subscription_id,
        )
        await apply_webhook_event(session, event)
        await session.commit()

        subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user.id))
        assert subscription is not None
        assert subscription.stripe_customer_id == customer_id
        assert subscription.stripe_subscription_id == subscription_id


async def test_webhook_subscription_updated_syncs_status(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        customer_id = f"cus_{uuid.uuid4().hex[:14]}"
        subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
        session.add(Subscription(user_id=user.id, stripe_customer_id=customer_id, stripe_subscription_id=subscription_id))
        await session.commit()

        event = _subscription_updated_event(
            event_id=f"evt_{uuid.uuid4().hex[:14]}",
            subscription_id=subscription_id,
            customer_id=customer_id,
            status="active",
        )
        await apply_webhook_event(session, event)
        await session.commit()

        subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user.id))
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.current_period_end is not None
        assert subscription.stripe_price_id == "price_test"


async def test_webhook_subscription_deleted_marks_canceled(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        customer_id = f"cus_{uuid.uuid4().hex[:14]}"
        subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
        session.add(
            Subscription(
                user_id=user.id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                status=SubscriptionStatus.ACTIVE,
            )
        )
        await session.commit()

        event = {
            "id": f"evt_{uuid.uuid4().hex[:14]}",
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": subscription_id, "customer": customer_id}},
        }
        await apply_webhook_event(session, event)
        await session.commit()

        subscription = await session.scalar(select(Subscription).where(Subscription.user_id == user.id))
        assert subscription.status == SubscriptionStatus.CANCELED


async def test_webhook_duplicate_event_id_is_ignored(client, _engine) -> None:
    async with await _session(_engine) as session:
        user = await _make_user(session)
        await session.commit()

        customer_id = f"cus_{uuid.uuid4().hex[:14]}"
        subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
        event_id = f"evt_{uuid.uuid4().hex[:14]}"
        event = _checkout_completed_event(
            event_id=event_id, user_id=user.id, customer_id=customer_id, subscription_id=subscription_id
        )
        await apply_webhook_event(session, event)
        await session.commit()

        # Redeliver the same event id with a different (bogus) customer — if
        # idempotency weren't working, this would create a second row.
        replay = _checkout_completed_event(
            event_id=event_id, user_id=user.id, customer_id="cus_should_be_ignored", subscription_id="sub_should_be_ignored"
        )
        await apply_webhook_event(session, replay)
        await session.commit()

        result = await session.scalars(select(Subscription).where(Subscription.user_id == user.id))
        subscriptions = result.all()
        assert len(subscriptions) == 1
        assert subscriptions[0].stripe_customer_id == customer_id
