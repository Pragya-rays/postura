from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("security_headers"):
        return None
    data = bundle.data_for("security_headers")
    # Modern equivalent of X-Frame-Options is CSP's frame-ancestors — either
    # one being present is enough to consider framing policy addressed.
    if data.get("xFrameOptions") or data.get("cspHasFrameAncestors"):
        return None
    return {"header": "x-frame-options", "present": False, "checkedUrl": data.get("checkedUrl")}


RULE = register(
    Rule(
        rule_id="hdr.xfo.missing",
        title="X-Frame-Options / frame-ancestors not set",
        category="Security Headers",
        severity=Severity.LOW,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N",
        cvss_score=3.1,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Add `X-Frame-Options: DENY` for legacy browser support.",
            "Add `frame-ancestors 'none'` to your CSP as the modern equivalent.",
        ],
        evaluate=_evaluate,
    )
)
