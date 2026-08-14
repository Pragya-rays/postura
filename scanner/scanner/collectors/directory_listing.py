"""Directory listing / information disclosure probe: request a short list of
commonly-forgotten paths and flag any that return an autoindex-style
listing. Verified tier only. Deliberately small, well-known candidate list —
this is a passive check on paths a legitimate scanner tool commonly probes,
not a brute-force directory buster.
"""
from __future__ import annotations

import httpx

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient, SSRFError

NAME = "directory_listing"

CANDIDATE_PATHS = [
    "/backup/",
    "/backups/",
    "/assets/backups/",
    "/uploads/",
    "/files/",
    "/.git/",
    "/old/",
    "/tmp/",
]

_INDEX_MARKERS = ("index of /", "<title>index of", "directory listing for")


async def _probe(client: GuardedAsyncClient, hostname: str, path: str) -> dict | None:
    for scheme in ("https", "http"):
        try:
            resp = await client.get(f"{scheme}://{hostname}{path}")
        except (httpx.RequestError, SSRFError):
            continue
        if resp.status_code == 200:
            body_lower = resp.text.lower()
            anchor_count = body_lower.count("<a href")
            if any(marker in body_lower for marker in _INDEX_MARKERS) or anchor_count >= 5:
                return {"path": path, "status": resp.status_code, "filesListed": anchor_count}
        break  # got a definitive response on this scheme; don't also try the other
    return None


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        found = [hit for path in CANDIDATE_PATHS if (hit := await _probe(client, ctx.hostname, path))]

    return {
        "checkedPaths": CANDIDATE_PATHS,
        "listingsFound": found,
        "hasDirectoryListing": len(found) > 0,
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.VERIFIED, run=collect)
