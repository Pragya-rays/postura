"""SSRF guard — the authoritative implementation (backend/app/security/ssrf.py
re-exports this). Every outbound request any collector makes goes through
GuardedAsyncClient, which validates the target BEFORE connecting and again on
every redirect hop — a redirect to a private IP is exactly as dangerous as
the original request pointing there.

Defense in depth, three layers:
  1. resolve_and_validate() resolves the hostname server-side and rejects it
     if ANY resolved address is private/loopback/link-local/reserved/
     multicast/unspecified — BEFORE any TCP connection is attempted. We
     validate the *resolved IP*, never the input string, which is why this
     also catches obfuscated literals (hex/octal/decimal IPs, IPv4-mapped
     IPv6) that a surface-level hostname regex would miss: however an
     attacker spells the target, whatever address it actually resolves to
     is what gets checked.
  2. GuardedAsyncClient re-runs that same check on every redirect hop (a 302
     to http://169.254.169.254/ is a classic SSRF bypass).
  3. After httpx actually connects, we inspect the negotiated peer IP and
     confirm it's one of the addresses we just validated for that hostname —
     closing the DNS-rebinding TOCTOU window where a name resolves
     differently between our pre-check and httpx's own internal connect-time
     resolution.

Known limitation (documented, not silently ignored): layer 3 depends on an
httpx/httpcore internals detail (`network_stream.get_extra_info("peername")`)
that isn't a stable public API and may not be reachable in every transport
configuration — if it isn't, the check simply skips itself rather than
failing closed on a false internals assumption. Layers 1+2 remain the
authoritative defense; layer 3 is best-effort hardening on top. For real
production hardening beyond MVP, pair this with container-level egress
restrictions (no network route from the scanner's container to RFC1918 /
link-local ranges).
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
import socket
from dataclasses import dataclass

import httpx

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

DEFAULT_CONNECT_TIMEOUT = 4.0
DEFAULT_TOTAL_TIMEOUT = 8.0
MAX_REDIRECTS = 5


class SSRFError(Exception):
    """Raised whenever a target is resolved-and-rejected, or a redirect/peer
    check fails post-connect. Callers (collectors, the domain-verification
    fetch, the backend's SSRF shim) all catch this and treat it as a hard
    stop — never a warning."""


@dataclass(frozen=True)
class ResolvedTarget:
    hostname: str
    ip: str
    port: int


def _allowed_scan_targets() -> set[str]:
    """Dev-only escape hatch, read directly from the environment so this
    framework-free package never depends on backend's pydantic Settings.
    NEVER set ALLOWED_SCAN_TARGETS in production."""
    raw = os.environ.get("ALLOWED_SCAN_TARGETS", "")
    return {h.strip().lower() for h in raw.split(",") if h.strip()}


def _is_blocked_ip(ip_obj: IPAddress) -> bool:
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None:
        ip_obj = ip_obj.ipv4_mapped
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local  # covers 169.254.0.0/16, incl. the 169.254.169.254 cloud metadata endpoint
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


async def resolve_and_validate(hostname: str, *, port: int) -> list[ResolvedTarget]:
    """Resolve `hostname` and raise SSRFError if any resolved address is
    disallowed. Returns every distinct resolved address (used by
    GuardedAsyncClient for the post-connect peer-IP check)."""
    hostname_clean = hostname.strip().lower().rstrip(".")
    if not hostname_clean:
        raise SSRFError("Empty hostname")

    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname_clean, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SSRFError(f"Could not resolve '{hostname_clean}': {exc}") from exc

    bypass = hostname_clean in _allowed_scan_targets()

    resolved: list[ResolvedTarget] = []
    seen_ips: set[str] = set()
    for _family, _type, _proto, _canonname, sockaddr in infos:
        ip_str = sockaddr[0]
        if ip_str in seen_ips:
            continue
        seen_ips.add(ip_str)

        if not bypass and _is_blocked_ip(ipaddress.ip_address(ip_str)):
            raise SSRFError(f"'{hostname_clean}' resolves to disallowed address {ip_str}")

        resolved.append(ResolvedTarget(hostname=hostname_clean, ip=ip_str, port=port))

    if not resolved:
        raise SSRFError(f"No usable addresses resolved for '{hostname_clean}'")
    return resolved


def _peer_ip(response: httpx.Response) -> str | None:
    """Best-effort extraction of the actually-connected peer IP. See module
    docstring's "known limitation" note — failure here degrades gracefully,
    it does not raise."""
    stream = response.extensions.get("network_stream")
    if stream is None:
        return None
    try:
        peername = stream.get_extra_info("peername")
    except Exception:
        return None
    if not peername:
        return None
    return peername[0]


class GuardedAsyncClient:
    """SSRF-safe httpx wrapper. Use as an async context manager:

        async with GuardedAsyncClient() as client:
            resp = await client.get("https://example.com/")

    `follow_redirects` is always False on the underlying httpx client —
    redirects are followed manually, hop by hop, re-validating the target on
    every hop, up to `max_redirects`.
    """

    def __init__(self, *, timeout: float = DEFAULT_TOTAL_TIMEOUT, max_redirects: int = MAX_REDIRECTS):
        self._timeout = httpx.Timeout(timeout, connect=min(DEFAULT_CONNECT_TIMEOUT, timeout))
        self._max_redirects = max_redirects
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GuardedAsyncClient":
        self._client = httpx.AsyncClient(follow_redirects=False, timeout=self._timeout)
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def get_no_redirect(self, url: str, **kwargs) -> httpx.Response:
        """Fetch exactly one hop without following a redirect further — still
        runs the SSRF pre-check for that hop. Used by collectors that need to
        inspect a redirect (e.g. does HTTP redirect to HTTPS) rather than
        follow it to completion."""
        if self._client is None:
            raise RuntimeError("GuardedAsyncClient must be used as `async with GuardedAsyncClient() as client:`")
        parsed = httpx.URL(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        await resolve_and_validate(parsed.host, port=port)
        return await self._client.request("GET", url, **kwargs)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        if self._client is None:
            raise RuntimeError("GuardedAsyncClient must be used as `async with GuardedAsyncClient() as client:`")

        current_url = httpx.URL(url)
        for hop in range(self._max_redirects + 1):
            port = current_url.port or (443 if current_url.scheme == "https" else 80)
            validated = await resolve_and_validate(current_url.host, port=port)
            allowed_ips = {t.ip for t in validated}

            response = await self._client.request(method, current_url, **kwargs)

            peer_ip = _peer_ip(response)
            if peer_ip is not None and peer_ip not in allowed_ips:
                await response.aclose()
                raise SSRFError(
                    f"Post-connect peer {peer_ip} for '{current_url.host}' did not match "
                    f"pre-validated addresses {sorted(allowed_ips)} — possible DNS rebinding"
                )

            if response.is_redirect and hop < self._max_redirects:
                location = response.headers.get("location")
                if not location:
                    return response
                current_url = response.url.join(location)
                continue

            return response

        raise SSRFError(f"Exceeded {self._max_redirects} redirects while fetching '{url}'")
