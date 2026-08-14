"""TLS certificate collector: issuer, subject, negotiated protocol version,
validity window, days remaining. Pure stdlib (ssl + socket) per spec — no
paid API needed for MVP.
"""
from __future__ import annotations

import asyncio
import socket
import ssl
from datetime import datetime, timezone

from scanner.collectors.base import CollectContext, CollectorSpec
from scanner.enums import ScanTier
from scanner.security.ssrf import resolve_and_validate

NAME = "tls_certificate"
_CERT_DATE_FORMAT = "%b %d %H:%M:%S %Y %Z"


def _parse_cert_date(value: str) -> datetime:
    return datetime.strptime(value, _CERT_DATE_FORMAT).replace(tzinfo=timezone.utc)


def _fetch_cert_sync(ip: str, hostname: str, port: int, timeout: float) -> dict:
    context = ssl.create_default_context()
    with socket.create_connection((ip, port), timeout=timeout) as raw_sock:
        with context.wrap_socket(raw_sock, server_hostname=hostname) as tls_sock:
            cert = tls_sock.getpeercert()
            protocol = tls_sock.version()
            cipher = tls_sock.cipher()

    not_after = _parse_cert_date(cert["notAfter"])
    not_before = _parse_cert_date(cert["notBefore"])
    issuer = dict(x[0] for x in cert.get("issuer", []))
    subject = dict(x[0] for x in cert.get("subject", []))
    days_remaining = (not_after - datetime.now(timezone.utc)).days

    return {
        "issuer": issuer.get("organizationName") or issuer.get("commonName") or "unknown",
        "subjectCommonName": subject.get("commonName"),
        "protocol": protocol,
        "cipherSuite": cipher[0] if cipher else None,
        "notBefore": not_before.isoformat(),
        "notAfter": not_after.isoformat(),
        "daysRemaining": days_remaining,
        "subjectAltNameCount": len(cert.get("subjectAltName", [])),
        "verified": True,  # ssl.create_default_context() raises on chain-verification failure below
    }


async def collect(ctx: CollectContext) -> dict:
    validated = await resolve_and_validate(ctx.hostname, port=443)
    ip = validated[0].ip
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _fetch_cert_sync, ip, ctx.hostname, 443, ctx.http_timeout)
    except ssl.SSLCertVerificationError as exc:
        return {"verified": False, "error": str(exc)}
    except (ssl.SSLError, OSError, TimeoutError) as exc:
        return {"verified": False, "reachable": False, "error": str(exc)}


SPEC = CollectorSpec(name=NAME, min_tier=ScanTier.PUBLIC, run=collect)
