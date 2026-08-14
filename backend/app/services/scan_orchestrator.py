"""Scan pipeline orchestrator: Collect -> Judge -> Explain -> Present, run
via FastAPI BackgroundTasks with its OWN DB session (the request's session
is closed by the time this runs). Commits after every stage transition so
GET /scans/:id polling — which runs in a separate request/session — sees
live progress under Postgres READ COMMITTED, instead of jumping straight
from "collecting" to "complete".

Explain calls run SEQUENTIALLY, not concurrently: a single AsyncSession is
not safe for concurrent use from multiple coroutines, and the explanation
cache needs the session for get/put. With at most 9 MVP findings and Gemini
calls at a few seconds each worst case, sequential still comfortably fits
the ~90s scan budget without risking session corruption for a marginal
speedup.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ai_engine.client import GeminiClient
from ai_engine.explain import explain_finding
from app.config import get_settings
from app.models.enums import ScanStatus
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_raw import ScanRaw
from app.services.cache_repo import SqlAlchemyExplanationCache
from scanner.collect import collect_all
from scanner.rules import engine as judge_engine  # noqa: F401 — import registers every rule
from scanner.rules.registry import get_rule
from scanner.rules.scoring import compute_grade, generate_summary

logger = logging.getLogger(__name__)
settings = get_settings()


def initial_stages() -> list[dict]:
    return [
        {"key": "collect", "label": "Collect", "status": "pending", "detail": None},
        {"key": "judge", "label": "Judge", "status": "pending", "detail": None},
        {"key": "explain", "label": "Explain", "status": "pending", "detail": None},
        {"key": "present", "label": "Present", "status": "pending", "detail": None},
    ]


def _with_stage(stages: list[dict], key: str, status: str, detail: str | None = None) -> list[dict]:
    """Returns a NEW list — JSONB columns don't track in-place mutation, so
    reassigning `scan.stages` to the result is what makes SQLAlchemy notice
    the change and include it in the next commit."""
    updated = []
    for stage in stages:
        if stage["key"] == key:
            new_stage = dict(stage)
            new_stage["status"] = status
            if detail is not None:
                new_stage["detail"] = detail
            updated.append(new_stage)
        else:
            updated.append(stage)
    return updated


def _gemini_client() -> GeminiClient | None:
    if not settings.gemini_api_key:
        return None
    return GeminiClient(
        api_key=settings.gemini_api_key, model=settings.gemini_model, timeout=settings.gemini_timeout_seconds
    )


async def run_scan_pipeline(scan_id: uuid.UUID, session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        scan = await session.scalar(select(Scan).where(Scan.id == scan_id).options(selectinload(Scan.domain)))
        if scan is None:
            logger.error("scan %s vanished before its pipeline could run", scan_id)
            return

        try:
            await _run(session, scan)
        except Exception:
            logger.exception("scan %s pipeline failed", scan_id)
            scan.status = ScanStatus.FAILED
            scan.stages = _with_stage(scan.stages, scan.current_stage or "collect", "error")
            await session.commit()


async def _run(session: AsyncSession, scan: Scan) -> None:
    hostname = scan.domain.hostname
    tier = scan.tier

    # --- Collect ---
    scan.current_stage = "collect"
    scan.stages = _with_stage(scan.stages, "collect", "active")
    await session.commit()

    raw_bundle = await collect_all(hostname, tier, http_timeout=settings.scan_http_timeout_seconds)
    for result in raw_bundle.results:
        session.add(
            ScanRaw(
                scan_id=scan.id,
                collector=result.collector,
                payload={"ok": result.ok, "data": result.data, "error": result.error},
            )
        )

    scan.stages = _with_stage(
        scan.stages,
        "collect",
        "done",
        detail=f"{raw_bundle.signal_count} signals gathered across {raw_bundle.collector_count} collectors",
    )
    await session.commit()

    # --- Judge ---
    scan.status = ScanStatus.JUDGING
    scan.current_stage = "judge"
    scan.stages = _with_stage(scan.stages, "judge", "active")
    await session.commit()

    findings = judge_engine.judge(raw_bundle, tier)

    scan.stages = _with_stage(
        scan.stages, "judge", "done", detail=f"{len(findings)} finding(s) produced by deterministic rules"
    )
    await session.commit()

    # --- Explain ---
    scan.status = ScanStatus.EXPLAINING
    scan.current_stage = "explain"
    scan.stages = _with_stage(scan.stages, "explain", "active")
    await session.commit()

    cache = SqlAlchemyExplanationCache(session)
    gemini = _gemini_client()

    explained = []
    for finding in findings:
        rule = get_rule(finding.rule_id)
        explained.append(await explain_finding(finding, rule, cache=cache, gemini=gemini))

    for finding, explanation in zip(findings, explained):
        session.add(
            Finding(
                scan_id=scan.id,
                rule_id=finding.rule_id,
                title=finding.title,
                category=finding.category,
                severity=finding.severity,
                cvss_vector=finding.cvss_vector,
                cvss_score=finding.cvss_score,
                owasp_category=finding.owasp_category,
                evidence=finding.evidence,
                simple_explanation=explanation.simple_explanation,
                technical_explanation=explanation.technical_explanation,
                remediation=finding.remediation,
                from_cache=explanation.from_cache,
            )
        )

    scan.stages = _with_stage(scan.stages, "explain", "done", detail="Plain-English + technical copy generated")
    await session.commit()

    # --- Present ---
    grade, score = compute_grade(findings)
    summary = generate_summary(hostname, grade, findings)

    scan.status = ScanStatus.COMPLETE
    scan.grade = grade
    scan.score = score
    scan.summary = summary
    scan.completed_at = datetime.now(timezone.utc)
    scan.current_stage = "present"
    scan.stages = _with_stage(scan.stages, "present", "done", detail=f"Grade {grade.value} · {score} / 100")
    await session.commit()
