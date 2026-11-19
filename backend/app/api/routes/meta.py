from fastapi import APIRouter
from sqlalchemy import String, cast, distinct, func, select

from app.api.deps import SessionDep
from app.core.catalog import CATEGORIES
from app.models import Guide, Run
from app.schemas import CategoryOut, PlatformStats

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/categories")
async def categories(session: SessionDep) -> list[CategoryOut]:
    counts = dict(
        (
            await session.execute(
                select(Guide.category, func.count())
                .where(Guide.status == "published")
                .group_by(Guide.category)
            )
        ).all()
    )
    return [CategoryOut(**c, count=counts.get(c["slug"], 0)) for c in CATEGORIES]


@router.get("/stats")
async def stats(session: SessionDep) -> PlatformStats:
    published = Guide.status == "published"
    guides, steps, authors = (
        await session.execute(
            select(
                func.count(),
                func.coalesce(func.sum(Guide.steps_count), 0),
                func.count(distinct(Guide.author_id)),
            ).where(published)
        )
    ).one()
    runs, completions = (
        await session.execute(
            select(func.count(), func.count().filter(Run.status == "completed")).select_from(Run)
        )
    ).one()
    learners = await session.scalar(
        select(func.count(distinct(func.coalesce(cast(Run.user_id, String), Run.anon_id))))
    )
    return PlatformStats(
        guides=guides,
        steps=int(steps),
        runs=runs,
        completions=completions,
        learners=learners or 0,
        authors=authors,
    )
