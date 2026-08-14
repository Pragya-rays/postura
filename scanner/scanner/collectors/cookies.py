"""Cookie flag collector: Secure, HttpOnly, SameSite on every Set-Cookie
header from the homepage response. Uses Headers.get_list() since a response
can set multiple cookies and httpx.Headers.get() would only return one.
"""
from __future__ import annotations

from http.cookies import SimpleCookie

from scanner.collectors.base import CollectContext, CollectorSpec, fetch_root
from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient

NAME = "cookies"


def _parse_cookie(raw: str) -> dict | None:
    jar = SimpleCookie()
    try:
        jar.load(raw)
    except Exception:
        return None
    for name, morsel in jar.items():
        return {
            "name": name,
            "secure": bool(morsel["secure"]),
            "httpOnly": bool(morsel["httponly"]),
            "sameSite": morsel["samesite"] or None,
        }
    return None


async def collect(ctx: CollectContext) -> dict:
    async with GuardedAsyncClient(timeout=ctx.http_timeout) as client:
        resp = await fetch_root(client, ctx.hostname)

    cookies = [parsed for raw in resp.headers.get_list("set-cookie") if (parsed := _parse_cookie(raw))]

    return {
        "checkedUrl": str(resp.url),
        "cookies": cookies,
        "cookieCount": len(cookies),
    }


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
