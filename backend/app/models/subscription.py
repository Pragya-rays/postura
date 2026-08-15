import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import SubscriptionStatus
from app.models.mixins import CreatedAtMixin, UpdatedAtMixin, UUIDPkMixin


class Subscription(UUIDPkMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """One row per user, created lazily on first Checkout attempt — a user
    with no row is on the Free plan, no upfront bookkeeping needed at
    registration. There's no `tier` column: Free vs. Pro is derived from
    `status` by app.services.billing.effective_tier, which is the one place
    that decision gets made."""

    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Null until Checkout actually completes (the customer can exist before
    # any subscription does — e.g. an abandoned Checkout session).
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    stripe_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus, name="subscription_status", native_enum=False),
        default=SubscriptionStatus.INCOMPLETE,
        nullable=False,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
