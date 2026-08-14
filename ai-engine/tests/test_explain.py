"""explain_finding orchestration tests: cache-hit, cache-miss+success,
cache-miss+garbage-output, cache-miss+Gemini-error, and gemini=None — all
against fake doubles, zero real network calls."""
from __future__ import annotations

import json

import pytest

import scanner.rules  # noqa: F401 — registers rules
from ai_engine.client import GeminiError
from ai_engine.explain import explain_finding
from ai_engine.fallback import FALLBACK
from scanner.enums import Severity
from scanner.models import EvaluatedFinding
from scanner.rules.registry import get_rule


class _Cached:
    def __init__(self, simple_text: str, technical_text: str):
        self.simple_text = simple_text
        self.technical_text = technical_text


class FakeCache:
    def __init__(self):
        self.store: dict[tuple[str, str], _Cached] = {}
        self.put_calls = 0

    async def get(self, rule_id: str, context_hash: str):
        return self.store.get((rule_id, context_hash))

    async def put(self, rule_id: str, context_hash: str, simple_text: str, technical_text: str) -> None:
        self.put_calls += 1
        self.store[(rule_id, context_hash)] = _Cached(simple_text, technical_text)


class FakeGemini:
    """Stand-in with the same shape as GeminiClient — explain.py only ever
    calls .generate_json(prompt), so a duck-typed fake is enough."""

    def __init__(self, response_text: str | None = None, raise_error: Exception | None = None):
        self._response_text = response_text
        self._raise_error = raise_error
        self.call_count = 0

    async def generate_json(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        if self._raise_error:
            raise self._raise_error
        return self._response_text


def _finding(rule_id: str, evidence: dict) -> EvaluatedFinding:
    rule = get_rule(rule_id)
    return EvaluatedFinding(
        rule_id=rule.rule_id,
        title=rule.title,
        category=rule.category,
        severity=rule.severity,
        cvss_vector=rule.cvss_vector,
        cvss_score=rule.cvss_score,
        owasp_category=rule.owasp_category,
        evidence=evidence,
        remediation=rule.remediation,
    )


VALID_GEMINI_JSON = json.dumps(
    {
        "simple_explanation": "A real Gemini-generated plain-English explanation of the problem for a website owner.",
        "technical_explanation": "A real Gemini-generated technical explanation referencing the relevant mechanism.",
    }
)


async def test_cache_hit_never_calls_gemini() -> None:
    rule = get_rule("hdr.hsts.missing")
    finding = _finding("hdr.hsts.missing", {"present": False})
    cache = FakeCache()
    gemini = FakeGemini(response_text=VALID_GEMINI_JSON)

    # Prime the cache directly, bypassing explain_finding.
    from ai_engine.cache import compute_context_hash

    context_hash = compute_context_hash(rule, finding.evidence)
    cache.store[(rule.rule_id, context_hash)] = _Cached("cached simple text", "cached technical text")

    result = await explain_finding(finding, rule, cache=cache, gemini=gemini)

    assert result.from_cache is True
    assert result.simple_explanation == "cached simple text"
    assert gemini.call_count == 0  # the whole point of the cache


async def test_cache_miss_success_calls_gemini_and_populates_cache() -> None:
    rule = get_rule("hdr.hsts.missing")
    finding = _finding("hdr.hsts.missing", {"present": False})
    cache = FakeCache()
    gemini = FakeGemini(response_text=VALID_GEMINI_JSON)

    result = await explain_finding(finding, rule, cache=cache, gemini=gemini)

    assert result.from_cache is False
    assert "real Gemini-generated" in result.simple_explanation
    assert gemini.call_count == 1
    assert cache.put_calls == 1


async def test_garbage_gemini_output_falls_back() -> None:
    rule = get_rule("hdr.hsts.missing")
    finding = _finding("hdr.hsts.missing", {"present": False})
    cache = FakeCache()
    gemini = FakeGemini(response_text="not even json {{{")

    result = await explain_finding(finding, rule, cache=cache, gemini=gemini)

    assert result.from_cache is False
    assert result.simple_explanation == FALLBACK["hdr.hsts.missing"].simple_explanation
    # Even on fallback, the result is still cached — the fallback text is
    # deterministic per rule/context, no reason to hit Gemini again.
    assert cache.put_calls == 1


async def test_gemini_output_failing_schema_validation_falls_back() -> None:
    rule = get_rule("hdr.hsts.missing")
    finding = _finding("hdr.hsts.missing", {"present": False})
    cache = FakeCache()
    # Valid JSON, but fails ExplanationOutput's min_length validator.
    gemini = FakeGemini(response_text=json.dumps({"simple_explanation": "too short", "technical_explanation": "too short"}))

    result = await explain_finding(finding, rule, cache=cache, gemini=gemini)

    assert result.from_cache is False
    assert result.simple_explanation == FALLBACK["hdr.hsts.missing"].simple_explanation


async def test_gemini_error_falls_back() -> None:
    rule = get_rule("hdr.hsts.missing")
    finding = _finding("hdr.hsts.missing", {"present": False})
    cache = FakeCache()
    gemini = FakeGemini(raise_error=GeminiError("simulated timeout"))

    result = await explain_finding(finding, rule, cache=cache, gemini=gemini)

    assert result.from_cache is False
    assert result.simple_explanation == FALLBACK["hdr.hsts.missing"].simple_explanation


async def test_gemini_none_uses_fallback_without_attempting_a_call() -> None:
    rule = get_rule("hdr.hsts.missing")
    finding = _finding("hdr.hsts.missing", {"present": False})
    cache = FakeCache()

    result = await explain_finding(finding, rule, cache=cache, gemini=None)

    assert result.from_cache is False
    assert result.simple_explanation == FALLBACK["hdr.hsts.missing"].simple_explanation
    assert cache.put_calls == 1


async def test_prompt_never_contains_raw_hostname_or_url() -> None:
    """The prompt-injection guard, made concrete: evidence containing a
    hostname/URL must not leak into what's sent to Gemini."""
    from ai_engine.prompt import render_prompt

    rule = get_rule("hdr.hsts.missing")
    finding = _finding(
        "hdr.hsts.missing", {"present": False, "checkedUrl": "https://attacker-controlled-content.example/inject"}
    )
    prompt = render_prompt(finding, rule)
    assert "attacker-controlled-content.example" not in prompt
