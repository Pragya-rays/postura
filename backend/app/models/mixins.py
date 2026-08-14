import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPkMixin:
    """UUID primary key, generated app-side so it's available before flush
    (e.g. for use in the same request before commit)."""

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class CreatedAtMixin:
    # timezone=True: stored/returned as tz-aware UTC so JSON serialization
    # produces an unambiguous ISO string (`...+00:00`) matching what the
    # frontend's `new Date(...)` expects, instead of a naive local timestamp.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
