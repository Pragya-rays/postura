from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("security_headers"):
        return None
    data = bundle.data_for("security_headers")
    if data.get("csp"):
        return None
    return {"header": "content-security-policy", "present": False, "checkedUrl": data.get("checkedUrl")}


RULE = register(
    Rule(
        rule_id="hdr.csp.missing",
        title="No Content-Security-Policy configured",
        category="Security Headers",
        severity=Severity.HIGH,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
        cvss_score=6.1,
        owasp_category="A03:2021 – Injection",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Start with a report-only policy: `Content-Security-Policy-Report-Only: default-src 'self'`.",
            "Inventory third-party scripts (analytics, chat widgets) and allowlist their exact origins.",
            "Move to enforcing mode once a week of reports shows no unexpected blocks.",
        ],
        evaluate=_evaluate,
    )
)
