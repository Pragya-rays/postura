import uuid

from app.models.enums import Severity
from app.schemas.base import CamelModel


class FindingOut(CamelModel):
    id: uuid.UUID
    scan_id: uuid.UUID
    rule_id: str
    title: str
    category: str
    severity: Severity
    cvss_vector: str
    cvss_score: float
    owasp_category: str
    evidence: dict
    simple_explanation: str
    technical_explanation: str
    remediation: list[str]
    from_cache: bool
