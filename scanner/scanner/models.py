"""Framework-free dataclasses shared across Collect and Judge. No web
framework or ORM dependency — the backend converts these to/from its own
SQLAlchemy models and Pydantic schemas at the boundary."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from scanner.enums import ScanTier, Severity


@dataclass
class CollectorResult:
    collector: str
    ok: bool
    data: dict = field(default_factory=dict)
    error: str | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RawBundle:
    """Output of the Collect stage: every collector's raw, opinion-free
    output for one scan. Judge reads from this; nothing here has decided
    whether anything is a vulnerability."""

    hostname: str
    tier: ScanTier
    results: list[CollectorResult] = field(default_factory=list)

    def get(self, collector_name: str) -> CollectorResult | None:
        return next((r for r in self.results if r.collector == collector_name), None)

    def data_for(self, collector_name: str) -> dict:
        """Convenience accessor for rules: returns {} for a missing or
        failed collector so a rule's evaluate() can use plain dict.get()
        without null-checking the collector result itself."""
        result = self.get(collector_name)
        return result.data if result and result.ok else {}

    def ok(self, collector_name: str) -> bool:
        result = self.get(collector_name)
        return bool(result and result.ok)

    @property
    def collector_count(self) -> int:
        return len(self.results)

    @property
    def signal_count(self) -> int:
        """Rough count of individual data points gathered — feeds the
        Collect stage's "N signals gathered across M collectors" detail
        string. Every successful collector contributes at least 1."""
        return sum(max(1, len(r.data)) for r in self.results if r.ok)


@dataclass
class EvaluatedFinding:
    """Output of the Judge stage for one rule that fired. Deterministic —
    produced entirely by scanner/rules/, never by an LLM."""

    rule_id: str
    title: str
    category: str
    severity: Severity
    cvss_vector: str
    cvss_score: float
    owasp_category: str
    evidence: dict
    remediation: list[str]
