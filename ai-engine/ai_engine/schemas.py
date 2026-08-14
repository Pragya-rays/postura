"""Strict schema for Gemini's structured output. This is the ONLY shape an
LLM call is allowed to produce — no severity, no CVSS, no remediation
steps, just prose explaining a finding Judge already decided is real.
Deliberately excludes remediation: see backend/app/models/explanation.py
for why copy-paste fix syntax is rule-authored, not AI-generated.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_HTML_TAG_RE = re.compile(r"<[^>]+>")


class ExplanationOutput(BaseModel):
    simple_explanation: str = Field(min_length=20, max_length=600)
    technical_explanation: str = Field(min_length=20, max_length=800)

    @field_validator("simple_explanation", "technical_explanation")
    @classmethod
    def _no_markup(cls, value: str) -> str:
        value = value.strip()
        if _HTML_TAG_RE.search(value):
            raise ValueError("explanation text must not contain HTML/markup")
        if "```" in value:
            raise ValueError("explanation text must not contain code fences")
        return value
