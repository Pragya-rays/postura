"""Table-driven Judge tests: synthetic RawBundle fixtures in, expected
finding (or None) out. Pure logic, zero network/DB — this is exactly the
kind of test the "Judge is deterministic" architectural claim should be
provable by.
"""
from __future__ import annotations

import dataclasses

import pytest

from scanner.enums import Grade, ScanTier, Severity
from scanner.models import CollectorResult, RawBundle
from scanner.rules import engine as judge_engine  # noqa: F401 — import registers every rule
from scanner.rules import registry
from scanner.rules.registry import all_rules
from scanner.rules.scoring import compute_grade, severity_breakdown


def _bundle(hostname: str, tier: ScanTier, **collector_data: dict | None) -> RawBundle:
    """Build a RawBundle from {collector_name: data_dict_or_None}. None means
    "this collector failed" (ok=False), matching how a real failed collector
    looks to Judge."""
    results = [
        CollectorResult(collector=name, ok=data is not None, data=data or {}, error=None if data is not None else "boom")
        for name, data in collector_data.items()
    ]
    return RawBundle(hostname=hostname, tier=tier, results=results)


CLEAN_HEADERS = {
    "checkedUrl": "https://clean.example/",
    "csp": "default-src 'self'; frame-ancestors 'none'",
    "hsts": "max-age=63072000",
    "xFrameOptions": "DENY",
    "xContentTypeOptions": "nosniff",
    "referrerPolicy": "no-referrer",
    "permissionsPolicy": "geolocation=()",
    "cspHasFrameAncestors": True,
}

MISSING_HEADERS = {
    "checkedUrl": "https://vulnerable.example/",
    "csp": None,
    "hsts": None,
    "xFrameOptions": None,
    "xContentTypeOptions": None,
    "referrerPolicy": None,
    "permissionsPolicy": None,
    "cspHasFrameAncestors": False,
}


@pytest.mark.parametrize(
    "rule_id,collectors,should_fire",
    [
        ("hdr.hsts.missing", {"security_headers": MISSING_HEADERS}, True),
        ("hdr.hsts.missing", {"security_headers": CLEAN_HEADERS}, False),
        ("hdr.csp.missing", {"security_headers": MISSING_HEADERS}, True),
        ("hdr.csp.missing", {"security_headers": CLEAN_HEADERS}, False),
        ("hdr.xfo.missing", {"security_headers": MISSING_HEADERS}, True),
        ("hdr.xfo.missing", {"security_headers": CLEAN_HEADERS}, False),
        # frame-ancestors alone (no X-Frame-Options) should also satisfy the rule
        (
            "hdr.xfo.missing",
            {"security_headers": {**MISSING_HEADERS, "cspHasFrameAncestors": True}},
            False,
        ),
        (
            "cookie.session.flags",
            {"cookies": {"cookies": [{"name": "session_id", "secure": False, "httpOnly": True, "sameSite": "None"}]}},
            True,
        ),
        (
            "cookie.session.flags",
            {"cookies": {"cookies": [{"name": "session_id", "secure": True, "httpOnly": True, "sameSite": "Lax"}]}},
            False,
        ),
        ("cookie.session.flags", {"cookies": {"cookies": []}}, False),
        ("dns.dmarc.missing", {"dns_records": {"dmarcPresent": False, "spfPresent": True, "dkimPresent": True}}, True),
        ("dns.dmarc.missing", {"dns_records": {"dmarcPresent": True, "spfPresent": True, "dkimPresent": True}}, False),
        (
            "tls.cert.expiry",
            {"tls_certificate": {"verified": True, "daysRemaining": 11, "issuer": "Let's Encrypt", "protocol": "TLSv1.3"}},
            True,
        ),
        (
            "tls.cert.expiry",
            {"tls_certificate": {"verified": True, "daysRemaining": 60, "issuer": "Let's Encrypt", "protocol": "TLSv1.3"}},
            False,
        ),
        ("tls.cert.expiry", {"tls_certificate": {"verified": False}}, False),
        (
            "fingerprint.tech.outdated",
            {"tech_fingerprint": {"jquery": {"detected": True, "version": "1.12.4"}}},
            True,
        ),
        (
            "fingerprint.tech.outdated",
            {"tech_fingerprint": {"jquery": {"detected": True, "version": "3.7.1"}}},
            False,
        ),
        (
            "cors.wildcard.credentials",
            {"cors_check": {"allowsWildcard": True, "accessControlAllowCredentials": True}},
            True,
        ),
        (
            "cors.wildcard.credentials",
            {"cors_check": {"reflectsArbitraryOrigin": True, "accessControlAllowCredentials": True}},
            True,
        ),
        (
            "cors.wildcard.credentials",
            {"cors_check": {"allowsWildcard": True, "accessControlAllowCredentials": False}},
            False,
        ),
        (
            "disclosure.directory.listing",
            {"directory_listing": {"listingsFound": [{"path": "/backups/", "status": 200, "filesListed": 14}]}},
            True,
        ),
        ("disclosure.directory.listing", {"directory_listing": {"listingsFound": []}}, False),
    ],
)
def test_rule_fires_as_expected(rule_id: str, collectors: dict, should_fire: bool) -> None:
    rule = next(r for r in all_rules() if r.rule_id == rule_id)
    bundle = _bundle("example.test", ScanTier.VERIFIED, **collectors)
    evidence = rule.evaluate(bundle)
    assert (evidence is not None) is should_fire


def test_rule_degrades_gracefully_when_its_collector_failed() -> None:
    """A rule whose collector failed must return None, not raise — Judge
    only ever asserts what it can support."""
    rule = next(r for r in all_rules() if r.rule_id == "hdr.hsts.missing")
    bundle = _bundle("example.test", ScanTier.VERIFIED, security_headers=None)
    assert rule.evaluate(bundle) is None


def _boom(_bundle: RawBundle) -> dict | None:
    raise RuntimeError("simulated rule bug")


def test_judge_skips_a_broken_rule_without_crashing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Rule is a frozen dataclass (deliberately immutable) — swap the
    # registered instance for a broken copy instead of patching an attribute.
    original = registry.get_rule("hdr.hsts.missing")
    broken = dataclasses.replace(original, evaluate=_boom)
    monkeypatch.setitem(registry._REGISTRY, "hdr.hsts.missing", broken)

    bundle = _bundle("example.test", ScanTier.VERIFIED, security_headers=MISSING_HEADERS)
    # Should not raise, and every other rule still evaluates normally.
    findings = judge_engine.judge(bundle, ScanTier.VERIFIED)
    assert all(f.rule_id != "hdr.hsts.missing" for f in findings)


def test_public_tier_excludes_verified_only_rules() -> None:
    bundle = _bundle(
        "example.test",
        ScanTier.PUBLIC,
        cors_check={"allowsWildcard": True, "accessControlAllowCredentials": True},
        directory_listing={"listingsFound": [{"path": "/backups/", "status": 200, "filesListed": 3}]},
    )
    findings = judge_engine.judge(bundle, ScanTier.PUBLIC)
    fired_ids = {f.rule_id for f in findings}
    assert "cors.wildcard.credentials" not in fired_ids
    assert "disclosure.directory.listing" not in fired_ids


def test_verified_tier_includes_verified_only_rules() -> None:
    bundle = _bundle(
        "example.test",
        ScanTier.VERIFIED,
        cors_check={"allowsWildcard": True, "accessControlAllowCredentials": True},
    )
    findings = judge_engine.judge(bundle, ScanTier.VERIFIED)
    assert any(f.rule_id == "cors.wildcard.credentials" for f in findings)


def test_findings_carry_static_remediation_not_evidence_dependent() -> None:
    rule = next(r for r in all_rules() if r.rule_id == "hdr.hsts.missing")
    bundle = _bundle("example.test", ScanTier.VERIFIED, security_headers=MISSING_HEADERS)
    findings = judge_engine.judge(bundle, ScanTier.VERIFIED)
    finding = next(f for f in findings if f.rule_id == "hdr.hsts.missing")
    assert finding.remediation == rule.remediation


def test_rule_ids_are_unique() -> None:
    ids = [r.rule_id for r in all_rules()]
    assert len(ids) == len(set(ids))


class TestScoring:
    def test_no_findings_is_grade_a(self) -> None:
        grade, score = compute_grade([])
        assert (grade, score) == (Grade.A, 100)

    def test_severity_breakdown_is_always_zero_filled(self) -> None:
        breakdown = severity_breakdown([])
        assert breakdown == {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    def test_score_floors_at_zero(self) -> None:
        from scanner.models import EvaluatedFinding

        findings = [
            EvaluatedFinding(
                rule_id=f"fake.{i}",
                title="x",
                category="x",
                severity=Severity.CRITICAL,
                cvss_vector="x",
                cvss_score=9.0,
                owasp_category="x",
                evidence={},
                remediation=[],
            )
            for i in range(5)
        ]
        grade, score = compute_grade(findings)
        assert score == 0
        assert grade == Grade.F
