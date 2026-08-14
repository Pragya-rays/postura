from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("security_headers"):
        return None
    data = bundle.data_for("security_headers")
    if data.get("hsts"):
        return None
    return {"header": "strict-transport-security", "present": False, "checkedUrl": data.get("checkedUrl")}


RULE = register(
    Rule(
        rule_id="hdr.hsts.missing",
        title="Strict-Transport-Security header is missing",
        category="Security Headers",
        severity=Severity.HIGH,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N",
        cvss_score=5.3,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Add `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` to every response.",
            "Confirm HTTPS is enforced on all subdomains before adding `includeSubDomains`.",
            "Submit the domain to the HSTS preload list once you've run it in production for a few weeks.",
        ],
        evaluate=_evaluate,
    )
)
