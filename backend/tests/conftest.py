"""Shared test fixtures. Requires a real (disposable) Postgres reachable at
DATABASE_URL — tables are created fresh for the test session and dropped at
the end; no external network calls happen anywhere in this suite (SSRF/DNS
calls are monkeypatched per-test where needed). See docs/README.md for how
to point this at a throwaway database.

NullPool + a session-per-request override (not one shared session for the
whole test): matches how `get_db` actually behaves in production — a fresh
AsyncSession per request. Sharing a single session/connection across
multiple sequential requests within a test was tried first and produced
intermittent asyncpg `InterfaceError: another operation is in progress`
once a background task (the scan pipeline) also touched the pool; NullPool
plus per-request sessions avoids any pooled-connection reuse across
operations entirely.
"""
from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db import Base, get_db

settings = get_settings()


@pytest_asyncio.fixture(scope="session")
async def _engine():
    import app.models  # noqa: F401 — registers every table onto Base.metadata;
    # without this import, Base.metadata is empty at this point (models are
    # only registered as a side effect of importing their modules) and
    # create_all silently creates zero tables.

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(_engine):
    from app.main import app

    session_factory = async_sessionmaker(bind=_engine, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
