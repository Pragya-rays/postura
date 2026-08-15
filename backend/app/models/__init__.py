"""Import every model here so `Base.metadata` is fully populated for Alembic
autogenerate and `create_all` (tests only — prod/dev always goes through
Alembic migrations)."""
from app.models.audit_log import AuditLog
from app.models.domain import Domain
from app.models.explanation import Explanation
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_raw import ScanRaw
from app.models.subscription import Subscription
from app.models.user import User

__all__ = ["AuditLog", "Domain", "Explanation", "Finding", "Scan", "ScanRaw", "Subscription", "User"]
