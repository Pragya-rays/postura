"""DNS records (A, AAAA, MX, NS, TXT, CAA) + SPF/DKIM/DMARC presence.

Not routed through the SSRF guard — this collector never connects to the
target's IP, only queries public DNS resolvers for record data, so it
carries none of the SSRF risk an HTTP fetch does.

DKIM presence is inherently best-effort without a known selector: we probe a
short list of common selectors (`default._domainkey.<host>` etc.) rather
than claiming certainty either way. Critically, a selector only counts as
"found" if the TXT content actually looks like a DKIM key record (contains
`v=dkim1` or a `p=` public-key parameter) — some DNS setups (wildcard
records, resolver hijacking/interception) return *something* for any
subdomain query, and treating mere non-emptiness as a hit produces false
positives. All queries run concurrently, not sequentially, both for latency
and so one slow/hanging query can't stall the rest.
"""
from __future__ import annotations

import asyncio
import re

import dns.asyncresolver
import dns.exception
import dns.resolver

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier

NAME = "dns_records"

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CAA"]
COMMON_DKIM_SELECTORS = ["default", "google", "selector1", "selector2", "dkim", "k1", "mail"]

# A `p=` tag with no value (`p=` followed by `;`, whitespace, or end-of-string)
# means the key has been REVOKED per RFC 6376 — some domains (notably
# example.com, seen during testing) publish a wildcard `v=DKIM1; p=` for
# every possible selector specifically to make probing look like "present".
# Require an actual base64 public-key value, not just the v=DKIM1 marker.
_DKIM_PUBKEY_RE = re.compile(r"p=([A-Za-z0-9+/]+=*)")


async def _query(resolver: dns.asyncresolver.Resolver, name: str, rtype: str) -> list[str]:
    try:
        answer = await resolver.resolve(name, rtype)
        return [rdata.to_text() for rdata in answer]
    except (
        dns.resolver.NXDOMAIN,
        dns.resolver.NoAnswer,
        dns.resolver.NoNameservers,
        dns.exception.Timeout,
    ):
        return []


def _looks_like_dkim_key(txt_records: list[str]) -> bool:
    joined = " ".join(txt_records)
    return bool(_DKIM_PUBKEY_RE.search(joined))


async def collect(ctx: CollectContext) -> dict:
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = ctx.http_timeout
    resolver.lifetime = ctx.http_timeout

    record_results = await asyncio.gather(*(_query(resolver, ctx.hostname, rtype) for rtype in RECORD_TYPES))
    records = dict(zip(RECORD_TYPES, record_results))

    txt_joined = " ".join(records.get("TXT", [])).lower()
    spf_present = "v=spf1" in txt_joined

    dmarc_query = _query(resolver, f"_dmarc.{ctx.hostname}", "TXT")
    dkim_queries = [_query(resolver, f"{selector}._domainkey.{ctx.hostname}", "TXT") for selector in COMMON_DKIM_SELECTORS]
    dmarc_records, *dkim_results = await asyncio.gather(dmarc_query, *dkim_queries)

    dmarc_present = any("v=dmarc1" in r.lower() for r in dmarc_records)
    dkim_selectors_found = [
        selector
        for selector, txt_records in zip(COMMON_DKIM_SELECTORS, dkim_results)
        if _looks_like_dkim_key(txt_records)
    ]

    return {
        "records": records,
        "spfPresent": spf_present,
        "dmarcPresent": dmarc_present,
        "dmarcRecords": dmarc_records,
        "dkimSelectorsChecked": COMMON_DKIM_SELECTORS,
        "dkimSelectorsFound": dkim_selectors_found,
        "dkimPresent": len(dkim_selectors_found) > 0,
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
