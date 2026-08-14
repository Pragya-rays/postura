from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register

_OUTDATED_MAJOR_VERSIONS = {"1", "2"}


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("tech_fingerprint"):
        return None
    data = bundle.data_for("tech_fingerprint")
    jquery = data.get("jquery") or {}
    version = jquery.get("version")
    if not jquery.get("detected") or not version:
        return None
    major = version.split(".")[0]
    if major not in _OUTDATED_MAJOR_VERSIONS:
        return None
    return {"library": "jquery", "version": version, "source": "script src fingerprint"}


RULE = register(
    Rule(
        rule_id="fingerprint.tech.outdated",
        title="Outdated jQuery version exposed in page source",
        category="Technology Fingerprint",
        severity=Severity.LOW,
        cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        cvss_score=3.4,
        owasp_category="A06:2021 – Vulnerable and Outdated Components",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Upgrade to a current jQuery 3.x release or drop the dependency if unused.",
            "Re-run this check after upgrading to confirm the fingerprint clears.",
        ],
        evaluate=_evaluate,
    )
)
