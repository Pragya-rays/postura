from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register

_SESSION_NAME_HINTS = ("session", "sid", "auth", "token")


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("cookies"):
        return None
    data = bundle.data_for("cookies")
    for cookie in data.get("cookies", []):
        name_lower = cookie["name"].lower()
        if not any(hint in name_lower for hint in _SESSION_NAME_HINTS):
            continue
        same_site = (cookie.get("sameSite") or "none").lower()
        if not cookie.get("secure") or same_site == "none":
            return {
                "cookie": cookie["name"],
                "secure": cookie.get("secure"),
                "httpOnly": cookie.get("httpOnly"),
                "sameSite": cookie.get("sameSite"),
            }
    return None


RULE = register(
    Rule(
        rule_id="cookie.session.flags",
        title="Session cookie missing SameSite and Secure flags",
        category="Cookies",
        severity=Severity.MEDIUM,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
        cvss_score=5.4,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Set `Secure` on every cookie that carries session state.",
            "Change `SameSite` to `Lax` (or `Strict` if no cross-site flows are needed).",
            "Re-issue existing sessions after the change so old cookies expire.",
        ],
        evaluate=_evaluate,
    )
)
