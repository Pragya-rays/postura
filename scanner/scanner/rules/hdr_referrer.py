from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("security_headers"):
        return None
    data = bundle.data_for("security_headers")
    if data.get("referrerPolicy"):
        return None
    return {"header": "referrer-policy", "present": False, "checkedUrl": data.get("checkedUrl")}


RULE = register(
    Rule(
        rule_id="hdr.referrer.missing",
        title="Referrer-Policy header is missing",
        category="Security Headers",
        severity=Severity.INFO,
        cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N",
        cvss_score=2.6,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Add `Referrer-Policy: strict-origin-when-cross-origin` — a safe, broadly-compatible default — to every response.",
            "Use a stricter value like `no-referrer` or `same-origin` if any URLs on the site carry sensitive query parameters.",
        ],
        evaluate=_evaluate,
    )
)
