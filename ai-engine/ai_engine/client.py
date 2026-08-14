"""Thin Gemini client. Talks to the Gemini REST API's structured-output mode
directly over HTTP (no google-genai SDK dependency, keeping ai-engine's
footprint small) and returns raw JSON text — explain.py is responsible for
Pydantic-validating it before it's trusted.
"""
from __future__ import annotations

import httpx

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

EXPLANATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "simple_explanation": {"type": "string"},
        "technical_explanation": {"type": "string"},
    },
    "required": ["simple_explanation", "technical_explanation"],
}


class GeminiError(Exception):
    """Raised on any Gemini API failure (network, non-2xx, malformed
    response shape). explain.py catches this uniformly alongside
    validation errors and falls back to static copy — Gemini being down or
    slow never blocks a scan from completing."""


class GeminiClient:
    def __init__(self, *, api_key: str, model: str = "gemini-flash-latest", timeout: float = 8.0):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def generate_json(self, prompt: str, *, response_schema: dict = EXPLANATION_RESPONSE_SCHEMA) -> str:
        """Returns the raw JSON text Gemini produced. Caller validates it —
        this method only guarantees "Gemini answered with 200 and something
        that looks like a text part", not that the content is well-formed."""
        if not self._api_key:
            raise GeminiError("No Gemini API key configured")

        url = f"{GEMINI_API_BASE}/models/{self._model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
                "temperature": 0.4,
                # Generous relative to the ~50-150 tokens the actual prose
                # needs: some Gemini model versions spend a chunk of the
                # budget on internal "thinking" tokens before any visible
                # output, and `thinkingConfig.thinkingBudget: 0` isn't
                # accepted by every model alias (400 INVALID_ARGUMENT was
                # observed during integration testing) — so we don't try to
                # disable thinking, we just leave enough room for it.
                "maxOutputTokens": 3072,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, params={"key": self._api_key}, json=payload)
        except httpx.RequestError as exc:
            raise GeminiError(f"Gemini request failed: {exc}") from exc

        if resp.status_code != 200:
            raise GeminiError(f"Gemini returned HTTP {resp.status_code}: {resp.text[:300]}")

        try:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise GeminiError(f"Unexpected Gemini response shape: {exc}") from exc

        return text
