"""Shared explanation cache contract + context_hash derivation. Deliberately
a Protocol, not a concrete implementation, so ai-engine stays unit-testable
without Postgres — the backend supplies the real SqlAlchemyExplanationCache
(backend/app/services/cache_repo.py).
"""
from __future__ import annotations

import hashlib
import json
from typing import Protocol

from scanner.rules.base import Rule


class CachedExplanation(Protocol):
    simple_text: str
    technical_text: str
    ai_generated: bool


class ExplanationCache(Protocol):
    async def get(self, rule_id: str, context_hash: str) -> CachedExplanation | None: ...

    async def put(
        self, rule_id: str, context_hash: str, simple_text: str, technical_text: str, ai_generated: bool
    ) -> None: ...


def compute_context_hash(rule: Rule, evidence: dict) -> str:
    """The cache key — and, not coincidentally, exactly what gets sent to
    Gemini as prompt input (see prompt.py). Using the SAME projection for
    both means: identical findings always get identical cache keys, AND the
    model never sees anything beyond what caching already requires it to be
    insensitive to (no raw URLs, no hostnames, no exact per-target values).
    That equivalence is what closes the prompt-injection door — there is no
    attacker-controlled free text anywhere in what Gemini receives.
    """
    signature = rule.cache_signature(evidence)
    canonical = json.dumps({"ruleId": rule.rule_id, **signature}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
