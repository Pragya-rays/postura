"""robots.txt / sitemap.xml presence + light parsing (disallow rule count,
sitemap references)."""
from __future__ import annotations

import httpx

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient, SSRFError

NAME = "robots_sitemap"


async def _try_fetch(client: GuardedAsyncClient, hostname: str, path: str) -> httpx.Response | None:
    for scheme in ("https", "http"):
        try:
            return await client.get(f"{scheme}://{hostname}{path}")
        except (httpx.RequestError, SSRFError):
            continue
    return None


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        robots = await _try_fetch(client, ctx.hostname, "/robots.txt")
        sitemap = await _try_fetch(client, ctx.hostname, "/sitemap.xml")

    robots_present = robots is not None and robots.status_code == 200
    sitemap_present = sitemap is not None and sitemap.status_code == 200

    disallow_count = 0
    sitemap_refs: list[str] = []
    if robots_present:
        for line in robots.text.splitlines():
            stripped = line.strip().lower()
            if stripped.startswith("disallow:"):
                disallow_count += 1
            elif stripped.startswith("sitemap:"):
                sitemap_refs.append(line.split(":", 1)[1].strip())

    return {
        "robotsPresent": robots_present,
        "robotsDisallowCount": disallow_count,
        "sitemapReferencedInRobots": sitemap_refs,
        "sitemapPresent": sitemap_present,
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
