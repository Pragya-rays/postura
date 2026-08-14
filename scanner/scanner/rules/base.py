"""The Judge contract. A Rule is entirely deterministic: `evaluate` is a
plain function of collected facts to evidence (or None). No AI, ever — that
is the one invariant this whole file exists to enforce structurally, not
just by convention.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle

# Returns an evidence dict if the rule fires, None if the target is clean —
# or evaluation couldn't be performed (e.g. the collector it depends on
# failed). A rule is never "wrong" for staying silent on missing evidence;
# Judge only ever asserts what it can actually support.
EvaluateFn = Callable[[RawBundle], "dict | None"]

# Projects raw evidence down to the fields that matter for caching/prompting
# — see scanner.rules.cache.compute_context_hash. Strips per-target noise
# (URLs, hostnames, exact dates) by default; rules with continuous evidence
# (e.g. "11 days until expiry") override this to bucket instead of strip.
CacheSignatureFn = Callable[[dict], dict]

_DEFAULT_NOISY_KEYS = {
    "checkedUrl",
    "hostname",
    "endpoint",
    "ip",
    "path",
    "notAfter",
    "notBefore",
    "record",
    "redirectLocation",
    "subjectCommonName",
}


def default_cache_signature(evidence: dict) -> dict:
    return {k: v for k, v in evidence.items() if k not in _DEFAULT_NOISY_KEYS}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    title: str
    category: str
    severity: Severity
    cvss_vector: str
    cvss_score: float
    owasp_category: str
    min_tier: ScanTier
    # Static, rule-authored fix steps — NOT AI-generated. See
    # backend/app/models/explanation.py for why: exact header/syntax
    # instructions are exactly what an LLM could plausibly hallucinate
    # wrong, which would be actively harmful advice from a security product.
    remediation: list[str]
    evaluate: EvaluateFn
    cache_signature: CacheSignatureFn = field(default=default_cache_signature)
