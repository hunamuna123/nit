from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import ExpertDep, SessionDep
from app.db import utcnow
from app.models import Guide, GuideVersion, Review
from app.schemas import ReviewIn, ReviewOut, ReviewQueueItem
from app.services.guides import cards_for, user_brief

router = APIRouter(prefix="/review", tags=["review"])


async def _review_out(session: SessionDep, r: Review) -> ReviewOut:
    v = await session.get(GuideVersion, r.version_id)
    return ReviewOut(
        id=r.id,
        guide_id=r.guide_id,
        version_number=v.number if v else 0,
        verdict=r.verdict,
        note=r.note,
        created_at=r.created_at,
        expert=user_brief(r.expert),
    )


@router.get("/queue")
async def queue(session: SessionDep, expert: ExpertDep) -> list[ReviewQueueItem]:
    stmt = select(Guide).where(
        Guide.status == "published",
        Guide.author_id != expert.id,
        (Guide.verified_version_id.is_(None))
        | (Guide.verified_version_id != Guide.published_version_id),
    )
    if expert.role != "admin":
        stmt = stmt.where(Guide.category.in_(expert.expert_categories or ["__none__"]))
    guides = list(await session.scalars(stmt.order_by(Guide.runs_count.desc())))
    last_reviews = {
        r.guide_id: r
        for r in await session.scalars(
            select(Review)
            .where(Review.guide_id.in_([g.id for g in guides]))
            .order_by(Review.created_at)
        )
    }
    cards = await cards_for(session, guides)
    out = []
    for g, card in zip(guides, cards, strict=True):
        v = await session.get(GuideVersion, g.published_version_id)
        last = last_reviews.get(g.id)
        if last and last.verdict == "changes" and last.version_id == g.published_version_id:
            reason = "changes_requested"
        elif g.verified_version_id:
            reason = "updated"
        else:
            reason = "new"
        out.append(
            ReviewQueueItem(guide=card, version_number=v.number if v else 0, reason=reason)  # type: ignore[arg-type]
        )
    return out


@router.get("/guides/{guide_id}")
async def guide_reviews(guide_id: int, session: SessionDep) -> list[ReviewOut]:
    rows = await session.scalars(
        select(Review)
        .where(Review.guide_id == guide_id)
        .options(selectinload(Review.expert))
        .order_by(Review.created_at.desc())
    )
    return [await _review_out(session, r) for r in rows]


@router.post("/guides/{guide_id}", status_code=status.HTTP_201_CREATED)
async def submit_review(
    guide_id: int, body: ReviewIn, session: SessionDep, expert: ExpertDep
) -> ReviewOut:
    g = await session.get(Guide, guide_id)
    if g is None or g.published_version_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Инструкция не найдена")
    if g.author_id == expert.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя проверять свою инструкцию")
    if expert.role != "admin" and g.category not in expert.expert_categories:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Это не ваша категория экспертизы")
    r = Review(
        guide_id=g.id,
        version_id=g.published_version_id,
        expert_id=expert.id,
        verdict=body.verdict,
        note=body.note,
    )
    session.add(r)
    if body.verdict == "approved":
        g.verified_by_id = expert.id
        g.verified_version_id = g.published_version_id
        g.verified_at = utcnow()
    await session.commit()
    r.expert = expert
    return await _review_out(session, r)
