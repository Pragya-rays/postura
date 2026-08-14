"""Judge stage. Importing this package registers every MVP rule (each rule
module calls registry.register() at import time) — explicit imports here,
not auto-discovery, so the rule set is greppable and a typo'd filename can't
silently vanish from the registry.
"""
from scanner.rules import (  # noqa: F401 — imported for registration side effects
    cookie_flags,
    cors_wildcard,
    directory_listing,
    dns_dmarc,
    fingerprint_outdated,
    hdr_csp,
    hdr_hsts,
    hdr_xfo,
    tls_expiry,
)

__all__ = [
    "cookie_flags",
    "cors_wildcard",
    "directory_listing",
    "dns_dmarc",
    "fingerprint_outdated",
    "hdr_csp",
    "hdr_hsts",
    "hdr_xfo",
    "tls_expiry",
]
