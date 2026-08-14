import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import Grade, ScanStatus, ScanTier
from app.models.mixins import UUIDPkMixin


class Scan(UUIDPkMixin, Base):
    """`created_at` doubles as `startedAt` on the wire, so this model defines
    it explicitly as `started_at` rather than using CreatedAtMixin."""

    __tablename__ = "scans"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ScanStatus] = mapped_column(
        SAEnum(ScanStatus, name="scan_status", native_enum=False), default=ScanStatus.QUEUED, nullable=False
    )
    tier: Mapped[ScanTier] = mapped_column(SAEnum(ScanTier, name="scan_tier", native_enum=False), nullable=False)
    grade: Mapped[Grade | None] = mapped_column(SAEnum(Grade, name="scan_grade", native_enum=False), nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Live pipeline progress — polled by GET /scans/:id. `stages` is a JSONB
    # array of {key, label, status, detail} matching the frontend's ScanStage[].
    current_stage: Mapped[str | None] = mapped_column(String(16), nullable=True)
    stages: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)

    # Present-stage one-sentence overview. Persisted (not computed on every
    # GET) so it stays stable, and defaults to "" so ScanReportOut.summary —
    # which the frontend types as a required string, never optional — has a
    # value even while the scan is still collecting/judging/explaining.
    summary: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    domain: Mapped["Domain"] = relationship(back_populates="scans")  # noqa: F821
    findings: Mapped[list["Finding"]] = relationship(  # noqa: F821
        back_populates="scan", cascade="all, delete-orphan"
    )
    raw_payloads: Mapped[list["ScanRaw"]] = relationship(  # noqa: F821
        back_populates="scan", cascade="all, delete-orphan"
    )

    @property
    def hostname(self) -> str:
        """Convenience accessor so ScanSummaryOut can read `hostname`
        directly via from_attributes — requires `domain` to be eager-loaded
        (selectinload), never accessed lazily in an async context."""
        return self.domain.hostname
