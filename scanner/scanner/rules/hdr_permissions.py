from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("security_headers"):
        return None
    data = bundle.data_for("security_headers")
    if data.get("permissionsPolicy"):
        return None
    return {"header": "permissions-policy", "present": False, "checkedUrl": data.get("checkedUrl")}


RULE = register(
    Rule(
        rule_id="hdr.permissions.missing",
        title="Permissions-Policy header is missing",
        category="Security Headers",
        severity=Severity.INFO,
        cvss_vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N",
        cvss_score=2.2,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Add a `Permissions-Policy` header that disables browser features the site doesn't use, e.g. `camera=(), microphone=(), geolocation=()`.",
            "Audit which features embedded third-party scripts (ads, widgets, analytics) actually need before locking the rest down.",
        ],
        evaluate=_evaluate,
    )
)
