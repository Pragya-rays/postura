"""Backend implementation of ai_engine.cache.ExplanationCache, backed by the
`explanations` table. Shared across ALL users — keyed by (rule_id,
context_hash), never by user or scan. Upserts idempotently since two
concurrent scans could race to cache the same (rule_id, context_hash).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.explanation import Explanation


class SqlAlchemyExplanationCache:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, rule_id: str, context_hash: str) -> Explanation | None:
        return await self._session.scalar(
            select(Explanation).where(Explanation.rule_id == rule_id, Explanation.context_hash == context_hash)
        )

    async def put(
        self, rule_id: str, context_hash: str, simple_text: str, technical_text: str, ai_generated: bool
    ) -> None:
        stmt = (
            pg_insert(Explanation)
            .values(
                rule_id=rule_id,
                context_hash=context_hash,
                simple_text=simple_text,
                technical_text=technical_text,
                ai_generated=ai_generated,
            )
            .on_conflict_do_update(
                index_elements=[Explanation.rule_id, Explanation.context_hash],
                set_={"simple_text": simple_text, "technical_text": technical_text, "ai_generated": ai_generated},
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
