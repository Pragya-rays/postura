import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import VerificationStatus
from app.schemas.base import CamelModel
from app.schemas.scan import ScanSummaryOut


class DomainIn(CamelModel):
    hostname: str = Field(min_length=1, max_length=255)


class DomainOut(CamelModel):
    id: uuid.UUID
    hostname: str
    verification_status: VerificationStatus
    verification_token: str
    added_at: datetime
    last_scan: ScanSummaryOut | None = None


class DomainVerifyOut(CamelModel):
    verification_status: VerificationStatus
    verified: bool
