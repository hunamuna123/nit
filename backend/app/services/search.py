# fts + опечатки (trgm) + вектора, склеиваем через rrf: 1/(60+rank)
# нет эмбеддингов - едет на первых двух

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, literal, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Guide
from app.services import ai

RRF_K = 60
POOL = 40
# подбирал руками под bge-m3, не трогать
SEM_MAX_DISTANCE = 0.6
SEM_BAND = 0.05


def _apply_filters[S: Select[*tuple[Any, ...]]](stmt: S, filters: dict[str, Any]) -> S:
    stmt = stmt.where(Guide.status == "published")
    if filters.get("category"):
        stmt = stmt.where(Guide.category == filters["category"])
    if filters.get("difficulty"):
        stmt = stmt.where(Guide.difficulty == filters["difficulty"])
    if filters.get("verified"):
        stmt = stmt.where(Guide.verified_version_id.is_not(None))
    if filters.get("max_minutes"):
        stmt = stmt.where(Guide.est_minutes <= filters["max_minutes"])
    if filters.get("author_id"):
        stmt = stmt.where(Guide.author_id == filters["author_id"])
    return stmt


async def hybrid_search(
    session: AsyncSession, q: str, filters: dict[str, Any]
) -> tuple[list[int], dict[int, str], list[str]]:
    q = q.strip()[:200]
    tsq = func.websearch_to_tsquery("russian", q)
    modes: list[str] = []
    ranks: dict[int, float] = {}

    def fuse(ids: Sequence[int], weight: float = 1.0) -> None:
        for rank, gid in enumerate(ids):
            ranks[gid] = ranks.get(gid, 0.0) + weight / (RRF_K + rank + 1)

    fts_stmt = _apply_filters(
        select(Guide.id)
        .where(Guide.search_tsv.op("@@")(tsq))
        .order_by(func.ts_rank_cd(Guide.search_tsv, tsq).desc())
        .limit(POOL),
        filters,
    )
    fts_ids = list(await session.scalars(fts_stmt))
    if fts_ids:
        modes.append("fts")
        fuse(fts_ids, 1.2)

    sim = func.greatest(
        func.word_similarity(literal(q), Guide.title),
        func.similarity(func.array_to_string(Guide.tags, " "), literal(q)),
    )
    fuzzy_stmt = _apply_filters(
        select(Guide.id).where(sim > 0.32).order_by(sim.desc()).limit(POOL), filters
    )
    fuzzy_ids = list(await session.scalars(fuzzy_stmt))
    if fuzzy_ids:
        modes.append("fuzzy")
        fuse(fuzzy_ids, 0.9)

    vector = await ai.embed_query(q)
    if vector is not None:
        dist = Guide.embedding.cosine_distance(vector)
        sem_stmt = _apply_filters(
            select(Guide.id, dist.label("d"))
            .where(Guide.embedding.is_not(None))
            .order_by(dist)
            .limit(POOL),
            filters,
        )
        rows = (await session.execute(sem_stmt)).all()
        best = min((d for _, d in rows if d is not None), default=1.0)
        limit = min(SEM_MAX_DISTANCE, best + SEM_BAND)
        sem_ids = [gid for gid, d in rows if d is not None and d <= limit]
        if sem_ids:
            modes.append("semantic")
            fuse(sem_ids, 1.0)

    ordered = sorted(ranks, key=lambda gid: ranks[gid], reverse=True)
    snippets = await _snippets(session, ordered[:30], q)
    return ordered, snippets, modes


async def _snippets(session: AsyncSession, ids: list[int], q: str) -> dict[int, str]:
    if not ids:
        return {}
    rows = await session.execute(
        text(
            "SELECT id, ts_headline('russian', search_text, websearch_to_tsquery('russian', :q), "
            "'StartSel=[[, StopSel=]], MaxWords=22, MinWords=10, MaxFragments=1, "
            "FragmentDelimiter= … ') FROM guides WHERE id = ANY(:ids) "
            "AND search_tsv @@ websearch_to_tsquery('russian', :q)"
        ),
        {"q": q, "ids": ids},
    )
    return {gid: snippet for gid, snippet in rows.all() if snippet and "[[" in snippet}
