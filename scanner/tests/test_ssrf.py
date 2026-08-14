"""Pure-logic SSRF guard tests. `asyncio.get_running_loop` is monkeypatched
to return a stub with a canned `getaddrinfo` — no real DNS resolution or
network I/O happens anywhere in this file, so it runs offline and
deterministically in CI.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket

import pytest

from scanner.security.ssrf import SSRFError, _is_blocked_ip, resolve_and_validate


class _StubLoop:
    def __init__(self, infos: list[tuple]):
        self._infos = infos

    async def getaddrinfo(self, host, port, *args, **kwargs):
        return self._infos


def _stub_resolution(monkeypatch: pytest.MonkeyPatch, ips: list[str], port: int = 443) -> None:
    infos = []
    for ip in ips:
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        sockaddr = (ip, port, 0, 0) if family == socket.AF_INET6 else (ip, port)
        infos.append((family, socket.SOCK_STREAM, 6, "", sockaddr))
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: _StubLoop(infos))


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",  # loopback
        "169.254.169.254",  # link-local / cloud metadata endpoint
        "169.254.0.1",  # link-local, general
        "10.0.0.5",  # RFC1918
        "192.168.1.1",  # RFC1918
        "172.16.0.1",  # RFC1918
        "0.0.0.0",  # unspecified
        "224.0.0.1",  # multicast
        "::1",  # IPv6 loopback
        "fe80::1",  # IPv6 link-local
        "fc00::1",  # IPv6 unique local
        "::ffff:127.0.0.1",  # IPv4-mapped IPv6 loopback
    ],
)
async def test_resolve_and_validate_blocks_disallowed_ips(monkeypatch: pytest.MonkeyPatch, ip: str) -> None:
    _stub_resolution(monkeypatch, [ip])
    with pytest.raises(SSRFError):
        await resolve_and_validate("evil.example", port=443)


async def test_resolve_and_validate_allows_public_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_resolution(monkeypatch, ["93.184.216.34"])  # a real-looking public IP
    resolved = await resolve_and_validate("example.com", port=443)
    assert len(resolved) == 1
    assert resolved[0].ip == "93.184.216.34"


async def test_resolve_and_validate_rejects_if_any_address_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """A multi-homed hostname where ONE of several resolved addresses is
    private must be rejected entirely, not just have the bad address
    filtered out — this is the guard against a target that's public today
    and rebinds to a private address on a later request."""
    _stub_resolution(monkeypatch, ["93.184.216.34", "10.0.0.5"])
    with pytest.raises(SSRFError):
        await resolve_and_validate("multi-homed.example", port=443)


async def test_allowed_scan_targets_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_SCAN_TARGETS", "internal-test.local, other.local")
    _stub_resolution(monkeypatch, ["127.0.0.1"])
    resolved = await resolve_and_validate("internal-test.local", port=8080)
    assert resolved[0].ip == "127.0.0.1"


async def test_allowed_scan_targets_is_case_and_whitespace_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_SCAN_TARGETS", "  Internal-Test.Local  ")
    _stub_resolution(monkeypatch, ["127.0.0.1"])
    resolved = await resolve_and_validate("internal-test.local", port=8080)
    assert resolved[0].ip == "127.0.0.1"


async def test_resolve_and_validate_empty_hostname_rejected() -> None:
    with pytest.raises(SSRFError):
        await resolve_and_validate("   ", port=443)


@pytest.mark.parametrize(
    "ip,expected",
    [
        ("8.8.8.8", False),
        ("1.1.1.1", False),
        ("127.0.0.1", True),
        ("10.1.2.3", True),
        ("169.254.169.254", True),
        ("::1", True),
        ("2606:4700:4700::1111", False),  # Cloudflare public resolver, IPv6
    ],
)
def test_is_blocked_ip(ip: str, expected: bool) -> None:
    assert _is_blocked_ip(ipaddress.ip_address(ip)) is expected
