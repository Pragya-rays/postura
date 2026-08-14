"""Basic technology fingerprint from response headers + page HTML: no
third-party Wappalyzer dependency, just a handful of well-known, cheap
signals (server/x-powered-by headers, generator meta tag, jQuery version
regex, common framework markers)."""
from __future__ import annotations

import re

from scanner.collectors.base import CollectContext, CollectorSpec, fetch_root
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient

NAME = "tech_fingerprint"

_JQUERY_RE = re.compile(r"jquery[-.]?(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)
_GENERATOR_RE = re.compile(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', re.IGNORECASE)


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        resp = await fetch_root(client, ctx.hostname)

    html = resp.text
    headers = resp.headers
    jquery_match = _JQUERY_RE.search(html)
    generator_match = _GENERATOR_RE.search(html)

    return {
        "checkedUrl": str(resp.url),
        "server": headers.get("server"),
        "xPoweredBy": headers.get("x-powered-by"),
        "generatorMeta": generator_match.group(1) if generator_match else None,
        "jquery": {
            "detected": bool(jquery_match),
            "version": jquery_match.group(1) if jquery_match else None,
        },
        "wordpress": "wp-content" in html or "wp-includes" in html,
        "nextJs": "__NEXT_DATA__" in html,
        "reactMarkers": 'id="root"' in html or "data-reactroot" in html,
        "angular": bool(re.search(r"ng-version", html)),
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
