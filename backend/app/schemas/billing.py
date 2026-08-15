from datetime import datetime

from app.models.enums import PlanTier, SubscriptionStatus
from app.schemas.base import CamelModel


class CheckoutSessionOut(CamelModel):
    url: str


class PortalSessionOut(CamelModel):
    url: str


class SubscriptionOut(CamelModel):
    tier: PlanTier
    status: SubscriptionStatus | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
