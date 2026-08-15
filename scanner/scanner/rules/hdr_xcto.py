from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("security_headers"):
        return None
    data = bundle.data_for("security_headers")
    if data.get("xContentTypeOptions"):
        return None
    return {"header": "x-content-type-options", "present": False, "checkedUrl": data.get("checkedUrl")}


RULE = register(
    Rule(
        rule_id="hdr.xcto.missing",
        title="X-Content-Type-Options header is missing",
        category="Security Headers",
        severity=Severity.LOW,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
        cvss_score=3.1,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Add `X-Content-Type-Options: nosniff` to every response.",
            "Confirm every response also sends an accurate `Content-Type` — nosniff only helps when the declared type is correct.",
        ],
        evaluate=_evaluate,
    )
)
