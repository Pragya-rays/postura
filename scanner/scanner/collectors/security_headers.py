"""Security response headers: CSP, HSTS, X-Frame-Options,
X-Content-Type-Options, Referrer-Policy, Permissions-Policy. Also records
whether the CSP (if any) sets frame-ancestors, since that's the modern
equivalent of X-Frame-Options and the xfo rule needs to know about both.
"""
from __future__ import annotations

from scanner.collectors.base import CollectContext, CollectorSpec, fetch_root
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient

NAME = "security_headers"

_HEADER_MAP = {
    "csp": "content-security-policy",
    "hsts": "strict-transport-security",
    "xFrameOptions": "x-frame-options",
    "xContentTypeOptions": "x-content-type-options",
    "referrerPolicy": "referrer-policy",
    "permissionsPolicy": "permissions-policy",
}


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        resp = await fetch_root(client, ctx.hostname)

    values = {key: resp.headers.get(header_name) for key, header_name in _HEADER_MAP.items()}
    csp_value = values.get("csp") or ""

    return {
        "checkedUrl": str(resp.url),
        "statusCode": resp.status_code,
        **values,
        "cspHasFrameAncestors": "frame-ancestors" in csp_value.lower(),
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
