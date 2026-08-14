from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("directory_listing"):
        return None
    data = bundle.data_for("directory_listing")
    listings = data.get("listingsFound") or []
    if not listings:
        return None
    first = listings[0]
    return {"path": first["path"], "status": first["status"], "filesListed": first["filesListed"]}


RULE = register(
    Rule(
        rule_id="disclosure.directory.listing",
        title="Directory listing enabled",
        category="Information Disclosure",
        severity=Severity.HIGH,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
        cvss_score=7.5,
        owasp_category="A01:2021 – Broken Access Control",
        min_tier=ScanTier.VERIFIED,
        remediation=[
            "Disable autoindexing on the web server (`Options -Indexes` on Apache, `autoindex off;` on nginx).",
            "Move backup archives and sensitive files outside the public web root entirely.",
            "Audit whether exposed files were already accessed and rotate any credentials they contain.",
        ],
        evaluate=_evaluate,
    )
)
