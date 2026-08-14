"""CORS misconfiguration probe: send a request with a foreign Origin header
and see whether the response reflects it back (wildcard or exact reflection)
alongside Access-Control-Allow-Credentials — the dangerous combination.
Verified tier only, since it's a slightly more active probe than a plain GET.
"""
from __future__ import annotations

import httpx

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient, SSRFError

NAME = "cors_check"
PROBE_ORIGIN = "https://postura-cors-probe.invalid"


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        headers = {"Origin": PROBE_ORIGIN}
        try:
            resp = await client.get(f"https://{ctx.hostname}/", headers=headers)
        except (httpx.RequestError, SSRFError):
            resp = await client.get(f"http://{ctx.hostname}/", headers=headers)

    acao = resp.headers.get("access-control-allow-origin")
    acac = (resp.headers.get("access-control-allow-credentials") or "").lower() == "true"

    return {
        "checkedUrl": str(resp.url),
        "probeOrigin": PROBE_ORIGIN,
        "accessControlAllowOrigin": acao,
        "accessControlAllowCredentials": acac,
        "allowsWildcard": acao == "*",
        "reflectsArbitraryOrigin": acao == PROBE_ORIGIN,
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.VERIFIED, run=collect)
