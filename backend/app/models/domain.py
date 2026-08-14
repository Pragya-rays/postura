import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import VerificationStatus
from app.models.mixins import UUIDPkMixin


class Domain(UUIDPkMixin, Base):
    """Named `added_at`, not `created_at` (no CreatedAtMixin) — matches the
    frontend's `addedAt` field name directly, so the Pydantic schema can
    read it via from_attributes without any renaming shim."""

    __tablename__ = "domains"
    __table_args__ = (UniqueConstraint("user_id", "hostname", name="uq_domains_user_hostname"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus, name="verification_status", native_enum=False),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
    )
    verification_token: Mapped[str] = mapped_column(String(64), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="domains")  # noqa: F821
    scans: Mapped[list["Scan"]] = relationship(  # noqa: F821
        back_populates="domain", cascade="all, delete-orphan", order_by="Scan.started_at.desc()"
    )

    @property
    def last_scan(self) -> "Scan | None":  # noqa: F821
        """Requires `scans` to be eager-loaded (selectinload) — `scans` is
        already ordered started_at DESC, so [0] is the most recent."""
        return self.scans[0] if self.scans else None
