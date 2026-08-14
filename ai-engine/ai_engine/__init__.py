"""Postura AI explain engine.

The only place in the system that touches an LLM. Takes structured Finding
metadata (never raw site content), returns Pydantic-validated explanation
copy, with hardcoded fallback text if the model call fails or returns
garbage. Built out fully in Phase 5 — this is a placeholder so the package
is importable/installable while backend scaffolding (Phase 1) stands up.
"""

__version__ = "0.1.0"
