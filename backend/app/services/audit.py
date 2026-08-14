"""Audit log writer. Called from auth, domain, and scan endpoints (Phase 2 +
Phase 6), and from SSRF-blocked attempts (Phase 7). Deliberately does not
commit — callers control the transaction boundary so an audit row and its
triggering change land in the same commit."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    target: str | None = None,
    ip_address: str | None = None,
    meta: dict | None = None,
) -> None:
    db.add(AuditLog(user_id=user_id, action=action, target=target, ip_address=ip_address, meta=meta))
    await db.flush()
