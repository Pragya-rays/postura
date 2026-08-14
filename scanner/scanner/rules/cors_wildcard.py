from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("cors_check"):
        return None
    data = bundle.data_for("cors_check")
    dangerous = (data.get("allowsWildcard") or data.get("reflectsArbitraryOrigin")) and data.get(
        "accessControlAllowCredentials"
    )
    if not dangerous:
        return None
    return {
        "header": "access-control-allow-origin",
        "value": data.get("accessControlAllowOrigin"),
        "allowCredentials": True,
        "checkedUrl": data.get("checkedUrl"),
    }


RULE = register(
    Rule(
        rule_id="cors.wildcard.credentials",
        title="CORS allows any origin alongside credentials",
        category="CORS",
        severity=Severity.CRITICAL,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        cvss_score=8.6,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.VERIFIED,
        remediation=[
            "Never combine a wildcard or reflected origin with `Allow-Credentials: true`.",
            "Maintain an explicit allowlist of trusted origins for any credentialed endpoint.",
            "Add a regression test that fails the build if a wildcard + credentials pair reappears.",
        ],
        evaluate=_evaluate,
    )
)
