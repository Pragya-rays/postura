import scanner.rules  # noqa: F401 — registers rules
from ai_engine.cache import compute_context_hash
from scanner.rules.registry import get_rule


def test_context_hash_is_order_independent() -> None:
    rule = get_rule("hdr.hsts.missing")
    h1 = compute_context_hash(rule, {"header": "strict-transport-security", "present": False, "checkedUrl": "https://a.example/"})
    h2 = compute_context_hash(rule, {"checkedUrl": "https://a.example/", "present": False, "header": "strict-transport-security"})
    assert h1 == h2


def test_context_hash_ignores_noisy_per_target_fields() -> None:
    """Two scans of DIFFERENT hostnames with the identical underlying
    finding must hash identically — that's the entire point of the shared
    cache."""
    rule = get_rule("hdr.hsts.missing")
    h1 = compute_context_hash(rule, {"header": "strict-transport-security", "present": False, "checkedUrl": "https://site-a.example/"})
    h2 = compute_context_hash(rule, {"header": "strict-transport-security", "present": False, "checkedUrl": "https://totally-different-site-b.example/"})
    assert h1 == h2


def test_context_hash_differs_across_rules() -> None:
    rule_a = get_rule("hdr.hsts.missing")
    rule_b = get_rule("hdr.csp.missing")
    evidence = {"present": False}
    assert compute_context_hash(rule_a, evidence) != compute_context_hash(rule_b, evidence)


def test_tls_expiry_buckets_days_remaining_instead_of_hashing_exact_value() -> None:
    """11 days and 13 days are both "urgent" (<7? no — both < 14 and >= 7 =
    "soon" bucket) and should hash identically; 2 days ("urgent") should
    hash differently from 13 days ("soon")."""
    rule = get_rule("tls.cert.expiry")
    soon_a = compute_context_hash(rule, {"daysRemaining": 11, "issuer": "Let's Encrypt", "protocol": "TLSv1.3"})
    soon_b = compute_context_hash(rule, {"daysRemaining": 13, "issuer": "Let's Encrypt", "protocol": "TLSv1.3"})
    urgent = compute_context_hash(rule, {"daysRemaining": 2, "issuer": "Let's Encrypt", "protocol": "TLSv1.3"})
    assert soon_a == soon_b
    assert soon_a != urgent
