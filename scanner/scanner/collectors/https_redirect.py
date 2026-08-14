"""HTTPS enforcement collector: does plain HTTP redirect to HTTPS, and is
HTTPS reachable at all. Uses get_no_redirect() to see the *first* hop rather
than following it — we only need to know whether the redirect target is
https, not resolve the whole chain.
"""
from __future__ import annotations

import httpx

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient, SSRFError

NAME = "https_redirect"


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        try:
            http_resp = await client.get_no_redirect(f"http://{ctx.hostname}/")
        except (httpx.RequestError, SSRFError) as exc:
            return {"httpReachable": False, "error": str(exc)}

        location = http_resp.headers.get("location")
        redirects_to_https = bool(
            http_resp.is_redirect and location and http_resp.url.join(location).scheme == "https"
        )

        https_reachable = False
        https_status = None
        try:
            https_resp = await client.get_no_redirect(f"https://{ctx.hostname}/")
            https_reachable = True
            https_status = https_resp.status_code
        except (httpx.RequestError, SSRFError):
            pass

        return {
            "httpReachable": True,
            "httpStatus": http_resp.status_code,
            "redirectsToHttps": redirects_to_https,
            "redirectLocation": location,
            "httpsReachable": https_reachable,
            "httpsStatus": https_status,
        }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
