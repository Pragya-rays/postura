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
    # Pro-gated fields: null for Free-tier users. Always fully populated in
    # the DB — get_scan() in routers/scans.py masks these on the way out
    # based on the requesting user's plan, never on write.
    cvss_vector: str | None
    cvss_score: float | None
    owasp_category: str | None
    evidence: dict | None
    simple_explanation: str
    technical_explanation: str | None
    remediation: list[str]
    from_cache: bool
    ai_generated: bool
