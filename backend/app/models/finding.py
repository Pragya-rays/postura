import uuid

from sqlalchemy import Boolean, Enum as SAEnum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import Severity
from app.models.mixins import CreatedAtMixin, UUIDPkMixin


class Finding(UUIDPkMixin, CreatedAtMixin, Base):
    """A single Judge output for one scan. `simple_explanation` /
    `technical_explanation` / `remediation` are a DENORMALIZED COPY of
    whatever the Explain stage produced (cached or fresh) at scan time — so a
    historical report never silently changes if the shared `explanations`
    cache entry is later regenerated."""

    __tablename__ = "findings"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[Severity] = mapped_column(SAEnum(Severity, name="finding_severity", native_enum=False), nullable=False)
    cvss_vector: Mapped[str] = mapped_column(String(64), nullable=False)
    cvss_score: Mapped[float] = mapped_column(Float, nullable=False)
    owasp_category: Mapped[str] = mapped_column(String(128), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False)

    simple_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    technical_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scan: Mapped["Scan"] = relationship(back_populates="findings")  # noqa: F821
