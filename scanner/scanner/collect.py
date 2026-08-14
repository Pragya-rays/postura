"""Collect stage entrypoint. Fans out every tier-applicable collector
concurrently via asyncio.gather; each collector is wrapped so its failure
never aborts the whole scan — a failed collector just produces a
CollectorResult(ok=False, error=...) that Judge treats as "insufficient
evidence" for any rule depending on it, rather than crashing the pipeline.
"""
from __future__ import annotations

import asyncio
import logging

from scanner.collectors import (
    cookies,
    cors_check,
    directory_listing,
    dns_records,
    https_redirect,
    robots_sitemap,
    security_headers,
    tech_fingerprint,
    tls_certificate,
    whois_lookup,
)
from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier
from scanner.models import CollectorResult, RawBundle

logger = logging.getLogger(__name__)

# Explicit list, not auto-discovery — greppable, and the order here is the
# order collectors run in (though they run concurrently, so order has no
# runtime effect beyond readability/log ordering).
ALL_SPECS: list[CollectorSpec] = [
    tls_certificate.SPEC,
    https_redirect.SPEC,
    security_headers.SPEC,
    cookies.SPEC,
    robots_sitemap.SPEC,
    dns_records.SPEC,
    whois_lookup.SPEC,
    tech_fingerprint.SPEC,
    cors_check.SPEC,
    directory_listing.SPEC,
]


def specs_for_tier(tier: ScanTier) -> list[CollectorSpec]:
    if tier == ScanTier.VERIFIED:
        return list(ALL_SPECS)
    return [s for s in ALL_SPECS if s.min_tier == ScanTier.PUBLIC]


async def _run_one(spec: CollectorSpec, ctx: CollectContext) -> CollectorResult:
    try:
        # Per-collector hard ceiling beyond its own internal timeouts, in
        # case a collector's own timeout handling has a gap (e.g. a hung
        # DNS query that ignores resolver.lifetime under some backends).
        data = await asyncio.wait_for(spec.run(ctx), timeout=ctx.http_timeout * 3)
        return CollectorResult(collector=spec.name, ok=True, data=data)
    except Exception as exc:  # noqa: BLE001 — a broken collector must never take the scan down with it
        logger.warning("collector %s failed for %s: %s", spec.name, ctx.hostname, exc)
        return CollectorResult(collector=spec.name, ok=False, error=str(exc))


async def collect_all(hostname: str, tier: ScanTier, *, http_timeout: float = 8.0) -> RawBundle:
    ctx = CollectContext(hostname=hostname, tier=tier, http_timeout=http_timeout)
    applicable = specs_for_tier(tier)
    results = await asyncio.gather(*(_run_one(spec, ctx) for spec in applicable))
    return RawBundle(hostname=hostname, tier=tier, results=list(results))
