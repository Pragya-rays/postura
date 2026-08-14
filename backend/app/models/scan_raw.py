import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPkMixin


class ScanRaw(UUIDPkMixin, CreatedAtMixin, Base):
    """One row per collector per scan. This is the audit trail — application
    code never deletes rows here, even if a scan or finding is later purged
    for other reasons."""

    __tablename__ = "scan_raw"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    collector: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    scan: Mapped["Scan"] = relationship(back_populates="raw_payloads")  # noqa: F821
