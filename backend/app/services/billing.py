"""Stripe integration + plan logic. This is the one place "what plan is this
user on" gets decided (effective_tier) and the one place Stripe's API is
called from — routers/billing.py is a thin HTTP wrapper around this module.

Webhook handling (apply_webhook_event) is deliberately synchronous DB logic
with no Stripe API calls of its own — it only ever reads the event payload
FastAPI already verified the signature on, so it's cheap to unit-test
against hand-built event dicts (see tests/test_billing.py).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.audit_log import AuditLog
from app.models.enums import PlanTier, SubscriptionStatus
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.billing import SubscriptionOut
from app.services.audit import write_audit_log

settings = get_settings()

_PRO_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}


class BillingNotConfigured(Exception):
    """Raised instead of letting a Stripe call fail confusingly when
    STRIPE_SECRET_KEY/STRIPE_PRICE_ID_PRO aren't set — fails closed with a
    clear message rather than a silent no-op or an opaque Stripe error."""


class NoStripeCustomer(Exception):
    """Raised by create_portal_session when the user has never started a
    Checkout session — there's nothing in the Portal to show them."""


async def _get_subscription(db: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    return await db.scalar(select(Subscription).where(Subscription.user_id == user_id))


def _tier_for_status(status: SubscriptionStatus | None) -> PlanTier:
    return PlanTier.PRO if status in _PRO_STATUSES else PlanTier.FREE


async def effective_tier(db: AsyncSession, user_id: uuid.UUID) -> PlanTier:
    subscription = await _get_subscription(db, user_id)
    return _tier_for_status(subscription.status if subscription else None)


async def get_subscription_out(db: AsyncSession, user_id: uuid.UUID) -> SubscriptionOut:
    subscription = await _get_subscription(db, user_id)
    if subscription is None:
        return SubscriptionOut(tier=PlanTier.FREE)
    return SubscriptionOut(
        tier=_tier_for_status(subscription.status),
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
    )


async def get_or_create_stripe_customer(db: AsyncSession, user: User) -> str:
    subscription = await _get_subscription(db, user.id)
    if subscription is not None:
        return subscription.stripe_customer_id

    stripe.api_key = settings.stripe_secret_key
    customer = await stripe.Customer.create_async(email=user.email, metadata={"user_id": str(user.id)})

    db.add(Subscription(user_id=user.id, stripe_customer_id=customer.id))
    await db.flush()
    return customer.id


async def create_checkout_session(db: AsyncSession, user: User) -> str:
    if not settings.stripe_secret_key or not settings.stripe_price_id_pro:
        raise BillingNotConfigured("Billing isn't configured yet — try again later.")

    customer_id = await get_or_create_stripe_customer(db, user)

    stripe.api_key = settings.stripe_secret_key
    session = await stripe.checkout.Session.create_async(
        mode="subscription",
        customer=customer_id,
        client_reference_id=str(user.id),
        line_items=[{"price": settings.stripe_price_id_pro, "quantity": 1}],
        success_url=f"{settings.frontend_url}/dashboard/billing?checkout=success",
        cancel_url=f"{settings.frontend_url}/dashboard/billing?checkout=cancelled",
    )
    return session.url


async def create_portal_session(db: AsyncSession, user: User) -> str:
    if not settings.stripe_secret_key:
        raise BillingNotConfigured("Billing isn't configured yet — try again later.")

    subscription = await _get_subscription(db, user.id)
    if subscription is None:
        raise NoStripeCustomer("No billing account yet — upgrade to Pro first.")

    stripe.api_key = settings.stripe_secret_key
    portal = await stripe.billing_portal.Session.create_async(
        customer=subscription.stripe_customer_id,
        return_url=f"{settings.frontend_url}/dashboard/billing",
    )
    return portal.url


# --- Webhook event handling -------------------------------------------------


async def apply_webhook_event(db: AsyncSession, event: dict) -> None:
    """Dispatches a verified Stripe event to the matching handler. Idempotent
    per event id: Stripe retries delivery on anything but a 2xx response, and
    an audit-log row keyed on the event id (written before any state change)
    doubles as the dedup marker — no separate table needed."""
    event_id = event.get("id") or ""
    event_type = event.get("type") or ""

    duplicate = await db.scalar(
        select(AuditLog.id).where(AuditLog.action == "billing.webhook.received", AuditLog.target == event_id)
    )
    if duplicate is not None:
        return
    await write_audit_log(db, action="billing.webhook.received", target=event_id, meta={"type": event_type})

    data = (event.get("data") or {}).get("object") or {}
    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(db, data)
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        # Stripe fires .created (not .updated) the first time Checkout
        # actually creates the subscription — same sync logic either way.
        await _handle_subscription_updated(db, data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(db, data)
    # Any other event type: acknowledged (the row above) and otherwise
    # ignored — never make Stripe retry an event we don't act on.


async def _handle_checkout_completed(db: AsyncSession, session_obj: dict) -> None:
    user_id_raw = session_obj.get("client_reference_id")
    customer_id = session_obj.get("customer")
    if not user_id_raw or not customer_id:
        return

    subscription = await db.scalar(select(Subscription).where(Subscription.stripe_customer_id == customer_id))
    if subscription is None:
        subscription = Subscription(user_id=uuid.UUID(user_id_raw), stripe_customer_id=customer_id)
        db.add(subscription)
    subscription.stripe_subscription_id = session_obj.get("subscription")
    # Status/price/period aren't in this payload — Stripe sends a
    # customer.subscription.updated event alongside this one that carries
    # them, handled below.
    await db.flush()


async def _handle_subscription_updated(db: AsyncSession, sub_obj: dict) -> None:
    subscription_id = sub_obj.get("id")
    subscription = await db.scalar(select(Subscription).where(Subscription.stripe_subscription_id == subscription_id))
    if subscription is None:
        subscription = await db.scalar(
            select(Subscription).where(Subscription.stripe_customer_id == sub_obj.get("customer"))
        )
    if subscription is None:
        # No matching customer — shouldn't happen if checkout.session.completed
        # landed first, but nothing to sync against if it didn't.
        return

    subscription.stripe_subscription_id = subscription_id
    try:
        subscription.status = SubscriptionStatus(sub_obj.get("status"))
    except ValueError:
        subscription.status = SubscriptionStatus.INCOMPLETE

    items = ((sub_obj.get("items") or {}).get("data")) or []
    if items:
        subscription.stripe_price_id = (items[0].get("price") or {}).get("id")

    # current_period_end lives on the subscription item in newer Stripe API
    # versions (a subscription can have items with different billing
    # periods) but on the subscription itself in older ones — check both.
    period_end = sub_obj.get("current_period_end")
    if period_end is None and items:
        period_end = items[0].get("current_period_end")
    subscription.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None
    subscription.cancel_at_period_end = bool(sub_obj.get("cancel_at_period_end"))
    await db.flush()


async def _handle_subscription_deleted(db: AsyncSession, sub_obj: dict) -> None:
    subscription = await db.scalar(
        select(Subscription).where(Subscription.stripe_subscription_id == sub_obj.get("id"))
    )
    if subscription is None:
        return
    subscription.status = SubscriptionStatus.CANCELED
    subscription.cancel_at_period_end = False
    await db.flush()
