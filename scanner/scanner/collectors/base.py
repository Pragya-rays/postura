"""Shared collector contract. Each module in scanner/collectors/ defines an
async `collect(ctx: CollectContext) -> dict` function and exports a
`SPEC = CollectorSpec(...)` describing it. The dict a collector returns is
raw, opinion-free JSON — Judge (scanner/rules/) is the only place that turns
it into a Finding.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from scanner.enums import ScanTier
from scanner.security.ssrf import GuardedAsyncClient, SSRFError


@dataclass(frozen=True)
class CollectContext:
    hostname: str
    tier: ScanTier
    http_timeout: float = 8.0


CollectFn = Callable[[CollectContext], Awaitable[dict]]


@dataclass(frozen=True)
class CollectorSpec:
    name: str
    # PUBLIC collectors always run. VERIFIED collectors only run once the
    # domain has proven ownership — see collect.py's tier filter.
    min_tier: ScanTier
    run: CollectFn


async def fetch_root(client: GuardedAsyncClient, hostname: str, *, path: str = "/") -> httpx.Response:
    """Try HTTPS first (the common case for anything worth grading), fall
    back to HTTP if HTTPS isn't reachable at all. Shared by collectors that
    just need "the homepage" rather than a specific redirect-chain inspection
    (https_redirect.py handles that separately)."""
    try:
        return await client.get(f"https://{hostname}{path}")
    except (httpx.RequestError, SSRFError):
        return await client.get(f"http://{hostname}{path}")
