"""explain_finding: the only function in this entire system allowed to call
an LLM. Cache-first, Gemini on a miss, hardcoded fallback on any failure —
Gemini being down, slow, or wrong never blocks a scan from completing, and
it never gets a vote on whether a finding is real (it's handed one that
Judge already decided on).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from pydantic import ValidationError

from ai_engine.cache import ExplanationCache, compute_context_hash
from ai_engine.client import GeminiClient, GeminiError
from ai_engine.fallback import FALLBACK, GENERIC_FALLBACK
from ai_engine.prompt import render_prompt
from ai_engine.schemas import ExplanationOutput
from scanner.models import EvaluatedFinding
from scanner.rules.base import Rule

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExplainedFinding:
    simple_explanation: str
    technical_explanation: str
    from_cache: bool


async def explain_finding(
    finding: EvaluatedFinding,
    rule: Rule,
    *,
    cache: ExplanationCache,
    gemini: GeminiClient | None,
) -> ExplainedFinding:
    context_hash = compute_context_hash(rule, finding.evidence)

    cached = await cache.get(rule.rule_id, context_hash)
    if cached is not None:
        return ExplainedFinding(cached.simple_text, cached.technical_text, from_cache=True)

    validated = await _generate(finding, rule, gemini)

    await cache.put(rule.rule_id, context_hash, validated.simple_explanation, validated.technical_explanation)
    return ExplainedFinding(validated.simple_explanation, validated.technical_explanation, from_cache=False)


async def _generate(finding: EvaluatedFinding, rule: Rule, gemini: GeminiClient | None) -> ExplanationOutput:
    if gemini is None:
        return FALLBACK.get(rule.rule_id, GENERIC_FALLBACK)

    try:
        prompt = render_prompt(finding, rule)
        raw = await gemini.generate_json(prompt)
        return ExplanationOutput.model_validate_json(raw)
    except (GeminiError, ValidationError, ValueError) as exc:
        logger.warning("Gemini explain failed for %s, using fallback: %s", rule.rule_id, exc)
        return FALLBACK.get(rule.rule_id, GENERIC_FALLBACK)
