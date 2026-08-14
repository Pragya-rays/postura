import uuid
from datetime import datetime

from app.models.enums import Grade, ScanStatus, ScanTier
from app.schemas.base import CamelModel


class StartScanIn(CamelModel):
    domain_id: uuid.UUID


class ScanStageOut(CamelModel):
    key: str
    label: str
    status: str
    detail: str | None = None


class ScanSummaryOut(CamelModel):
    id: uuid.UUID
    domain_id: uuid.UUID
    hostname: str
    status: ScanStatus
    tier: ScanTier
    grade: Grade | None = None
    score: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
