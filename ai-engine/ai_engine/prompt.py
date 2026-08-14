"""Renders ai_engine/prompts/finding_explain.txt. The rendered prompt
contains ONLY structured finding metadata plus the rule's cache_signature
projection of evidence — never the target hostname/URL, never raw
HTTP/HTML content. That's what closes the prompt-injection door: there is
no attacker-controlled free text anywhere in what Gemini receives, because
the target's own page content never enters the prompt at all.
"""
from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from jinja2 import Template

from scanner.models import EvaluatedFinding
from scanner.rules.base import Rule


@lru_cache(maxsize=1)
def _template() -> Template:
    text = resources.files("ai_engine").joinpath("prompts", "finding_explain.txt").read_text(encoding="utf-8")
    return Template(text)


def render_prompt(finding: EvaluatedFinding, rule: Rule) -> str:
    context = rule.cache_signature(finding.evidence)
    return _template().render(
        rule_id=rule.rule_id,
        title=rule.title,
        category=rule.category,
        severity=finding.severity.value,
        cvss_vector=finding.cvss_vector,
        cvss_score=finding.cvss_score,
        owasp_category=rule.owasp_category,
        context_json=json.dumps(context, sort_keys=True, default=str),
    )
