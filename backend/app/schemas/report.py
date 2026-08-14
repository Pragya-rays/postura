from app.schemas.base import CamelModel
from app.schemas.finding import FindingOut
from app.schemas.scan import ScanStageOut, ScanSummaryOut


class ScanReportOut(CamelModel):
    scan: ScanSummaryOut
    stages: list[ScanStageOut]
    summary: str
    findings: list[FindingOut]
    severity_breakdown: dict[str, int]
