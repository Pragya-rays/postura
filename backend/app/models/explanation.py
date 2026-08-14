from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import CreatedAtMixin, UUIDPkMixin


class Explanation(UUIDPkMixin, CreatedAtMixin, Base):
    """Shared explanation cache, keyed by (rule_id, context_hash) — NOT by
    user or scan. Identical findings across every user in the system reuse
    this row instead of calling Gemini again. See
    ai_engine.cache.compute_context_hash for how context_hash is derived.

    Only prose (simple_text/technical_text) is AI-generated and cached here.
    Remediation steps are deliberately NOT part of the AI output — they're
    static, rule-authored content (scanner.rules.base.Rule.remediation),
    because copy-paste fix syntax (exact header names/values) is exactly the
    kind of thing an LLM could plausibly hallucinate wrong, which would be
    actively harmful advice from a security product. Findings.remediation
    is populated straight from the Rule at Judge time, no AI, no cache."""

    __tablename__ = "explanations"
    __table_args__ = (UniqueConstraint("rule_id", "context_hash", name="uq_explanations_rule_context"),)

    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    simple_text: Mapped[str] = mapped_column(Text, nullable=False)
    technical_text: Mapped[str] = mapped_column(Text, nullable=False)
