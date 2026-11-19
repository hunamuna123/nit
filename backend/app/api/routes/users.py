from fastapi import APIRouter, HTTPException, status
from sqlalchemy import String, cast, distinct, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, SessionDep
from app.api.routes.studio import suggestion_out
from app.core.catalog import CATEGORY_SLUGS
from app.db import utcnow
from app.models import Bookmark, Comment, Guide, Run, Suggestion, User
from app.schemas import (
    DashboardOut,
    DashboardRun,
    ExpertRequestIn,
    ProfileOut,
    ProfileStats,
    ProfileUpdateIn,
    UserMe,
)
from app.services.guides import cards_for, usefulness_sql, user_brief
from app.services.runs import run_brief

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}")
async def profile(user_id: int, session: SessionDep) -> ProfileOut:
    u = await session.get(User, user_id)
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    guides = list(
        await session.scalars(
            select(Guide)
            .where(Guide.author_id == u.id, Guide.status == "published")
            .order_by(usefulness_sql().desc())
        )
    )
    completed = await session.scalar(
        select(func.count()).where(Run.user_id == u.id, Run.status == "completed")
    )
    accepted = await session.scalar(
        select(func.count()).where(Suggestion.user_id == u.id, Suggestion.status == "accepted")
    )
    comments = await session.scalar(
        select(func.count()).where(Comment.user_id == u.id, Comment.is_hidden.is_(False))
    )
    helped = await session.scalar(
        select(func.count(distinct(func.coalesce(cast(Run.user_id, String), Run.anon_id))))
        .join(Guide, Guide.id == Run.guide_id)
        .where(Guide.author_id == u.id, Run.status == "completed")
    )
    return ProfileOut(
        user=user_brief(u),
        bio=u.bio,
        created_at=u.created_at,
        stats=ProfileStats(
            completed=completed or 0,
            authored=len(guides),
            accepted_suggestions=accepted or 0,
            comments=comments or 0,
            learners_helped=helped or 0,
        ),
        guides=await cards_for(session, guides),
    )


@router.get("/me/dashboard")
async def dashboard(session: SessionDep, user: CurrentUserDep) -> DashboardOut:
    runs = list(
        await session.scalars(
            select(Run).where(Run.user_id == user.id).order_by(Run.last_activity_at.desc())
        )
    )
    latest: dict[int, Run] = {}
    for r in runs:
        latest.setdefault(r.guide_id, r)
    guides = {
        g.id: g for g in await session.scalars(select(Guide).where(Guide.id.in_(list(latest))))
    }
    cards = {c.id: c for c in await cards_for(session, list(guides.values()))}
    active, completed = [], []
    for gid, r in latest.items():
        g = guides.get(gid)
        if g is None or g.status != "published":
            continue
        item = DashboardRun(
            run=await run_brief(session, r, g),
            guide=cards[gid],
            last_activity_at=r.last_activity_at,
            completed_at=r.completed_at,
        )
        (completed if r.status == "completed" else active).append(item)

    marked = list(
        await session.scalars(
            select(Guide)
            .join(Bookmark, Bookmark.guide_id == Guide.id)
            .where(Bookmark.user_id == user.id, Guide.status == "published")
            .order_by(Bookmark.created_at.desc())
        )
    )
    mine = (
        await session.execute(
            select(Suggestion, Guide)
            .join(Guide, Guide.id == Suggestion.guide_id)
            .where(Suggestion.user_id == user.id)
            .options(selectinload(Suggestion.user))
            .order_by(Suggestion.created_at.desc())
            .limit(20)
        )
    ).all()
    return DashboardOut(
        active=active,
        completed=completed,
        bookmarks=await cards_for(session, marked),
        suggestions=[await suggestion_out(session, s, g) for s, g in mine],
    )


@router.patch("/me")
async def update_me(body: ProfileUpdateIn, session: SessionDep, user: CurrentUserDep) -> UserMe:
    user.name, user.bio = body.name, body.bio
    await session.commit()
    return UserMe.model_validate(user)


@router.post("/me/expert-request")
async def expert_request(
    body: ExpertRequestIn, session: SessionDep, user: CurrentUserDep
) -> UserMe:
    if user.role in ("expert", "admin"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Вы уже эксперт")
    cats = [c for c in body.categories if c in CATEGORY_SLUGS]
    if not cats:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Выберите категории")
    user.expert_request_status = "pending"
    user.expert_request_text = body.text
    user.expert_request_categories = cats
    user.expert_requested_at = utcnow()
    await session.commit()
    return UserMe.model_validate(user)
