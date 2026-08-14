from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule
from scanner.rules.registry import register


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("dns_records"):
        return None
    data = bundle.data_for("dns_records")
    if data.get("dmarcPresent"):
        return None
    return {
        "record": f"_dmarc.{bundle.hostname}",
        "found": False,
        "spf": data.get("spfPresent", False),
        "dkim": data.get("dkimPresent", False),
    }


RULE = register(
    Rule(
        rule_id="dns.dmarc.missing",
        title="No DMARC record published",
        category="Email Authentication",
        severity=Severity.MEDIUM,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N",
        cvss_score=4.3,
        owasp_category="A05:2021 – Security Misconfiguration",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Publish `v=DMARC1; p=none; rua=mailto:dmarc-reports@<yourdomain>` first to gather data.",
            "Review aggregate reports for two weeks, then move policy to `p=quarantine`.",
            "Graduate to `p=reject` once legitimate senders are all aligned.",
        ],
        evaluate=_evaluate,
    )
)
