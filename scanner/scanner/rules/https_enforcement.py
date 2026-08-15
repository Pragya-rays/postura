from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("https_redirect"):
        return None
    data = bundle.data_for("https_redirect")
    # No plain-HTTP listener to downgrade from — nothing to flag here (the
    # tls_certificate collector's own rule covers HTTPS itself being broken).
    if not data.get("httpReachable") or data.get("redirectsToHttps"):
        return None
    return {
        "httpStatus": data.get("httpStatus"),
        "redirectLocation": data.get("redirectLocation"),
        "httpsReachable": data.get("httpsReachable"),
    }


RULE = register(
    Rule(
        rule_id="tls.https.not_enforced",
        title="Plain HTTP is not redirected to HTTPS",
        category="SSL / TLS",
        severity=Severity.HIGH,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N",
        cvss_score=5.3,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Redirect every plain-HTTP request to its HTTPS equivalent with a 301 — at the load balancer/web server level, not in application code.",
            "Add `Strict-Transport-Security` once the redirect is confirmed working, so repeat visits skip the insecure request entirely.",
            "Re-run this check after deploying to confirm the redirect target is `https://` and not a loop.",
        ],
        evaluate=_evaluate,
    )
)
