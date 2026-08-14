"""Domain ownership verification: a DNS TXT record OR a /.well-known file,
either containing the domain's verification_token. Both paths go through
the SSRF guard exactly like every other outbound request the scanner makes
— verification itself is not exempt from that discipline.

- DNS: a TXT record at `_postura-challenge.<hostname>` containing the token.
- File: `https://<hostname>/.well-known/postura-<token>.txt` whose body
  contains the token.
"""
from __future__ import annotations

import dns.asyncresolver
import dns.exception
import dns.resolver
import httpx

from app.security.ssrf import GuardedAsyncClient, SSRFError

_TIMEOUT = 8.0


async def _check_dns_txt(hostname: str, token: str) -> bool:
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = _TIMEOUT
    resolver.lifetime = _TIMEOUT
    try:
        answer = await resolver.resolve(f"_postura-challenge.{hostname}", "TXT")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout):
        return False
    return any(token in rdata.to_text() for rdata in answer)


async def _check_well_known_file(hostname: str, token: str) -> bool:
    async with GuardedAsyncClient(timeout=_TIMEOUT) as client:
        for scheme in ("https", "http"):
            try:
                resp = await client.get(f"{scheme}://{hostname}/.well-known/postura-{token}.txt")
            except (httpx.RequestError, SSRFError):
                continue
            if resp.status_code == 200 and token in resp.text:
                return True
    return False


async def verify_domain_ownership(hostname: str, token: str) -> bool:
    if await _check_dns_txt(hostname, token):
        return True
    return await _check_well_known_file(hostname, token)
