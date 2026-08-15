"""Full pipeline test: Collect is mocked (no real network) and Gemini is
forced to None (deterministic fallback copy), so status transitions, report
assembly, and cache reuse are tested without depending on any external
service.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.enums import SubscriptionStatus
from app.models.subscription import Subscription
from app.models.user import User
from app.security.ssrf import ResolvedTarget
from scanner.enums import ScanTier
from scanner.models import CollectorResult, RawBundle


def _fake_bundle(hostname: str) -> RawBundle:
    return RawBundle(
        hostname=hostname,
        tier=ScanTier.PUBLIC,
        results=[
            CollectorResult(
                collector="security_headers",
                ok=True,
                data={
                    "checkedUrl": f"https://{hostname}/",
                    "csp": None,
                    "hsts": None,
                    "xFrameOptions": None,
                    "xContentTypeOptions": None,
                    "referrerPolicy": None,
                    "permissionsPolicy": None,
                    "cspHasFrameAncestors": False,
                },
            ),
            CollectorResult(collector="cookies", ok=True, data={"cookies": [], "cookieCount": 0}),
            CollectorResult(collector="tls_certificate", ok=False, data={}, error="simulated failure"),
            CollectorResult(
                collector="dns_records", ok=True, data={"dmarcPresent": True, "spfPresent": True, "dkimPresent": True}
            ),
            CollectorResult(collector="tech_fingerprint", ok=True, data={"jquery": {"detected": False, "version": None}}),
            CollectorResult(
                collector="https_redirect",
                ok=True,
                data={"httpReachable": True, "httpStatus": 200, "redirectsToHttps": True},
            ),
            CollectorResult(collector="robots_sitemap", ok=True, data={"robotsPresent": False, "sitemapPresent": False}),
            CollectorResult(collector="whois_lookup", ok=True, data={"found": True}),
        ],
    )


async def _fake_collect_all(hostname: str, tier, **kwargs) -> RawBundle:
    return _fake_bundle(hostname)


async def _make_pro(_engine, email: str) -> None:
    """This file tests pipeline mechanics (Collect -> Judge -> Explain ->
    Present shape), not billing — every test user is put on Pro so none of
    it is incidentally gated by Free-tier limits (technical explanations
    being masked, the 5-scans/month cap, etc.)."""
    session_factory = async_sessionmaker(bind=_engine, expire_on_commit=False)
    async with session_factory() as session:
        user = await session.scalar(select(User).where(User.email == email))
        session.add(
            Subscription(
                user_id=user.id,
                stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:10]}",
                stripe_subscription_id=f"sub_test_{uuid.uuid4().hex[:10]}",
                status=SubscriptionStatus.ACTIVE,
            )
        )
        await session.commit()


async def _register_and_add_domain(client, monkeypatch: pytest.MonkeyPatch, hostname: str, _engine) -> str:
    email = f"test-{uuid.uuid4().hex[:10]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "correct-horse-battery-staple"})
    await _make_pro(_engine, email)

    async def _fake_resolve(hostname_: str, *, port: int):
        return [ResolvedTarget(hostname=hostname_, ip="93.184.216.34", port=port)]

    monkeypatch.setattr("app.routers.domains.resolve_and_validate", _fake_resolve)
    resp = await client.post("/domains", json={"hostname": hostname})
    return resp.json()["id"]


async def test_full_pipeline_completes_with_expected_shape(client, monkeypatch: pytest.MonkeyPatch, _engine) -> None:
    hostname = f"pipeline-test-{uuid.uuid4().hex[:8]}.example"

    monkeypatch.setattr("app.services.scan_orchestrator.collect_all", _fake_collect_all)
    monkeypatch.setattr("app.services.scan_orchestrator._gemini_client", lambda: None)

    domain_id = await _register_and_add_domain(client, monkeypatch, hostname, _engine)

    start_resp = await client.post("/scans", json={"domainId": domain_id})
    assert start_resp.status_code == 201
    assert start_resp.json()["status"] == "collecting"  # never "queued" — matches the frontend mock contract
    scan_id = start_resp.json()["id"]

    report_resp = await client.get(f"/scans/{scan_id}")
    assert report_resp.status_code == 200
    report = report_resp.json()

    assert report["scan"]["status"] == "complete"
    assert report["scan"]["grade"] is not None
    assert all(stage["status"] == "done" for stage in report["stages"])
    assert set(report["severityBreakdown"].keys()) == {"critical", "high", "medium", "low", "info"}
    assert len(report["findings"]) >= 2  # hsts + csp (+ xfo) fire from the fake bundle
    assert all(f["simpleExplanation"] and f["technicalExplanation"] for f in report["findings"])
    assert all(f["remediation"] for f in report["findings"])
    assert report["summary"]

    # findings sorted worst-severity-first
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    ranks = [severity_rank[f["severity"]] for f in report["findings"]]
    assert ranks == sorted(ranks)


async def test_identical_finding_reuses_cache_across_scans(client, monkeypatch: pytest.MonkeyPatch, _engine) -> None:
    monkeypatch.setattr("app.services.scan_orchestrator.collect_all", _fake_collect_all)
    monkeypatch.setattr("app.services.scan_orchestrator._gemini_client", lambda: None)

    # Not asserting report1's fromCache here: the `explanations` cache is
    # process-wide (by design — shared across every user/scan) and this test
    # DB isn't rolled back between tests, so an earlier test in the same run
    # may have already warmed these exact rule_id/context_hash entries. What
    # this test actually proves is order-independent: a SECOND scan with
    # identical underlying evidence always reuses whatever's cached.
    hostname1 = f"cache-test-a-{uuid.uuid4().hex[:8]}.example"
    domain_id_1 = await _register_and_add_domain(client, monkeypatch, hostname1, _engine)
    scan1 = await client.post("/scans", json={"domainId": domain_id_1})
    report1 = (await client.get(f"/scans/{scan1.json()['id']}")).json()

    # Different user, different hostname, but IDENTICAL underlying evidence
    # (the fake bundle only varies by hostname via `checkedUrl`, which the
    # cache signature strips as noise) — this must hit the shared cache.
    hostname2 = f"cache-test-b-{uuid.uuid4().hex[:8]}.example"
    domain_id_2 = await _register_and_add_domain(client, monkeypatch, hostname2, _engine)
    scan2 = await client.post("/scans", json={"domainId": domain_id_2})
    report2 = (await client.get(f"/scans/{scan2.json()['id']}")).json()
    assert all(f["fromCache"] is True for f in report2["findings"])

    text_by_rule_1 = {f["ruleId"]: f["simpleExplanation"] for f in report1["findings"]}
    for finding in report2["findings"]:
        assert finding["simpleExplanation"] == text_by_rule_1[finding["ruleId"]]


async def test_scans_require_auth(client) -> None:
    resp = await client.get("/scans")
    assert resp.status_code == 401


async def test_start_scan_for_nonexistent_domain_404s(client) -> None:
    email = f"test-{uuid.uuid4().hex[:10]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "correct-horse-battery-staple"})

    resp = await client.post("/scans", json={"domainId": str(uuid.uuid4())})
    assert resp.status_code == 404
