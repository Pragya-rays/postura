"""Async SQLAlchemy engine/session setup. One engine per process, one session
per request via the get_db dependency; the scan orchestrator opens its own
session from `async_session_factory` since it runs outside request scope.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Declarative base shared by every model in app/models/."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, closed automatically."""
    async with async_session_factory() as session:
        yield session
