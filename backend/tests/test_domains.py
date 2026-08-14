"""Domain CRUD + the SSRF pre-check. Malicious-target tests use IP literals
(169.254.169.254, 127.0.0.1) which getaddrinfo resolves locally with no real
DNS lookup — genuinely network-free. The "successful add" test monkeypatches
resolve_and_validate since a real hostname would need real DNS.
"""
from __future__ import annotations

import uuid

import pytest

from app.security.ssrf import ResolvedTarget, SSRFError


async def _register(client) -> None:
    email = f"test-{uuid.uuid4().hex[:10]}@example.com"
    resp = await client.post("/auth/register", json={"email": email, "password": "correct-horse-battery-staple"})
    assert resp.status_code == 201


@pytest.mark.parametrize("malicious_hostname", ["169.254.169.254", "127.0.0.1", "10.0.0.5", "0.0.0.0"])
async def test_malicious_targets_rejected_before_any_row_created(client, malicious_hostname: str) -> None:
    await _register(client)

    resp = await client.post("/domains", json={"hostname": malicious_hostname})
    assert resp.status_code == 422

    listing = await client.get("/domains")
    assert listing.json() == []


async def test_add_domain_succeeds_and_appears_in_listing(client, monkeypatch: pytest.MonkeyPatch) -> None:
    await _register(client)

    async def _fake_resolve(hostname: str, *, port: int):
        return [ResolvedTarget(hostname=hostname, ip="93.184.216.34", port=port)]

    monkeypatch.setattr("app.routers.domains.resolve_and_validate", _fake_resolve)

    resp = await client.post("/domains", json={"hostname": "example.com"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["hostname"] == "example.com"
    assert body["verificationStatus"] == "unverified"
    assert body["verificationToken"].startswith("postura-verify-")
    assert body["lastScan"] is None

    listing = await client.get("/domains")
    assert len(listing.json()) == 1
    assert listing.json()[0]["hostname"] == "example.com"


async def test_duplicate_domain_for_same_user_rejected(client, monkeypatch: pytest.MonkeyPatch) -> None:
    await _register(client)

    async def _fake_resolve(hostname: str, *, port: int):
        return [ResolvedTarget(hostname=hostname, ip="93.184.216.34", port=port)]

    monkeypatch.setattr("app.routers.domains.resolve_and_validate", _fake_resolve)

    first = await client.post("/domains", json={"hostname": "duplicate-test.example"})
    assert first.status_code == 201
    second = await client.post("/domains", json={"hostname": "duplicate-test.example"})
    assert second.status_code == 400


async def test_domains_require_auth(client) -> None:
    resp = await client.get("/domains")
    assert resp.status_code == 401


async def test_verify_unverified_domain_returns_pending(client, monkeypatch: pytest.MonkeyPatch) -> None:
    await _register(client)

    async def _fake_resolve(hostname: str, *, port: int):
        return [ResolvedTarget(hostname=hostname, ip="93.184.216.34", port=port)]

    async def _fake_verify(hostname: str, token: str) -> bool:
        return False

    monkeypatch.setattr("app.routers.domains.resolve_and_validate", _fake_resolve)
    monkeypatch.setattr("app.routers.domains.verify_domain_ownership", _fake_verify)

    created = await client.post("/domains", json={"hostname": "unverifiable.example"})
    domain_id = created.json()["id"]

    resp = await client.post(f"/domains/{domain_id}/verify")
    assert resp.status_code == 200
    assert resp.json() == {"verificationStatus": "pending", "verified": False}
