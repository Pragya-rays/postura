"""WHOIS lookup via python-whois. The library is synchronous and talks to
TLD-specific WHOIS servers over its own socket calls (not the target site's
webserver), so it sits outside the HTTP SSRF guard's threat model — but it's
also notoriously flaky (missing servers, malformed responses, rate limits),
so failures degrade to `{"found": False}` rather than aborting the scan.
"""
from __future__ import annotations

import asyncio

import whois

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier

NAME = "whois_lookup"


def _to_iso(value):
    if isinstance(value, list):
        value = value[0] if value else None
    return value.isoformat() if hasattr(value, "isoformat") else value


def _lookup_sync(hostname: str) -> dict:
    result = whois.whois(hostname)
    return {
        "found": bool(result.get("domain_name")),
        "registrar": result.get("registrar"),
        "creationDate": _to_iso(result.get("creation_date")),
        "expirationDate": _to_iso(result.get("expiration_date")),
        "updatedDate": _to_iso(result.get("updated_date")),
        "nameServers": result.get("name_servers"),
        "status": result.get("status"),
    }


async def collect(ctx: CollectContext) -> dict:
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(None, _lookup_sync, ctx.hostname), timeout=ctx.http_timeout * 2
        )
    except Exception as exc:
        return {"found": False, "error": str(exc)}


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
