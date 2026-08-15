import json

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.billing import CheckoutSessionOut, PortalSessionOut, SubscriptionOut
from app.services import billing
from app.services.audit import write_audit_log

router = APIRouter(prefix="/billing", tags=["billing"])
settings = get_settings()


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await billing.get_subscription_out(db, user.id)


@router.post("/checkout-session", response_model=CheckoutSessionOut)
async def checkout_session(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        url = await billing.create_checkout_session(db, user)
    except billing.BillingNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    await write_audit_log(db, action="billing.checkout_started", user_id=user.id)
    await db.commit()
    return CheckoutSessionOut(url=url)


@router.post("/portal-session", response_model=PortalSessionOut)
async def portal_session(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        url = await billing.create_portal_session(db, user)
    except billing.BillingNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except billing.NoStripeCustomer as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    await db.commit()
    return PortalSessionOut(url=url)


@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Billing isn't configured yet.")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        # construct_event both verifies the signature and validates the
        # payload is well-formed JSON; its return value (a stripe.Event) is
        # discarded, though — that type's dict-like interface isn't stable
        # across stripe-python versions (`.get()` broke between SDK
        # releases), so apply_webhook_event works off a plain dict parsed
        # from the same already-verified payload instead.
        stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload or signature")

    event = json.loads(payload)
    await billing.apply_webhook_event(db, event)
    await db.commit()
    return {"received": True}
