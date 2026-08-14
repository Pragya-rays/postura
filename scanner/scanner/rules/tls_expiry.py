from scanner.enums import ScanTier, Severity
from scanner.models import RawBundle
from scanner.rules.base import Rule, default_cache_signature
from scanner.rules.registry import register

# Matches the reference finding text ("within the 14-day warning threshold")
# — a real deployment might tune this, but 14 days is the MVP baseline.
WARNING_THRESHOLD_DAYS = 14


def _evaluate(bundle: RawBundle) -> dict | None:
    if not bundle.ok("tls_certificate"):
        return None
    data = bundle.data_for("tls_certificate")
    days_remaining = data.get("daysRemaining")
    if not data.get("verified") or days_remaining is None or days_remaining >= WARNING_THRESHOLD_DAYS:
        return None
    return {
        "issuer": data.get("issuer"),
        "notAfter": data.get("notAfter"),
        "protocol": data.get("protocol"),
        "daysRemaining": days_remaining,
    }


def _cache_signature(evidence: dict) -> dict:
    """Bucket the continuous daysRemaining value instead of stripping it —
    the exact day count is noisy (every scan of the same cert on a
    different day would otherwise get a different cache key), but the
    urgency tier is exactly what the explanation copy needs to stay
    accurate without being regenerated daily."""
    days = evidence.get("daysRemaining")
    base = default_cache_signature({k: v for k, v in evidence.items() if k != "daysRemaining"})
    if days is None:
        bucket = "unknown"
    elif days <= 0:
        bucket = "expired"
    elif days < 7:
        bucket = "urgent"
    else:
        bucket = "soon"
    return {**base, "expiryBucket": bucket}


RULE = register(
    Rule(
        rule_id="tls.cert.expiry",
        title="TLS certificate is expiring soon",
        category="SSL / TLS",
        severity=Severity.MEDIUM,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L",
        cvss_score=3.7,
        owasp_category="A02:2021 – Cryptographic Failures",
        min_tier=ScanTier.PUBLIC,
        remediation=[
            "Confirm auto-renewal (certbot / ACME client) is actually running and not silently failing.",
            "Add an expiry monitor with at least a 21-day lead time.",
            "Renew manually now if automation can't be confirmed before the deadline.",
        ],
        evaluate=_evaluate,
        cache_signature=_cache_signature,
    )
)
