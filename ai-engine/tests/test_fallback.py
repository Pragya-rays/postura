import pytest

import scanner.rules  # noqa: F401 — registers rules
from ai_engine.fallback import check_fallback_coverage


def test_every_registered_rule_has_fallback_copy() -> None:
    """The real assertion: this must pass with the actual rule registry, not
    a mock — a new rule shipped without fallback copy should fail CI."""
    check_fallback_coverage()  # raises RuntimeError if anything is missing


def test_missing_fallback_is_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_engine import fallback

    monkeypatch.setitem(fallback.FALLBACK, "__never_used__", fallback.FALLBACK["hdr.hsts.missing"])
    monkeypatch.delitem(fallback.FALLBACK, "hdr.hsts.missing")
    with pytest.raises(RuntimeError, match="hdr.hsts.missing"):
        check_fallback_coverage()
