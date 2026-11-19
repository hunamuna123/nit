from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, SessionDep, ViewerDep
from app.models import Bookmark, Comment, Guide, Rating, StepVote, Suggestion, User
from app.schemas import (
    BookmarkOut,
    CommentIn,
    CommentOut,
    CreatedOut,
    GuideCard,
    GuideDetail,
    GuideList,
    RatingIn,
    RatingOut,
    RunOut,
    StepPublicStats,
    SuggestionIn,
    VersionBrief,
    VoteIn,
    VoteOut,
)
from app.services import search
from app.services.guides import (
    cards_for,
    fork_guide,
    get_published_guide,
    get_version,
    list_versions,
    step_out,
    usefulness_sql,
    user_brief,
    version_brief,
)
from app.services.runs import latest_run, new_run, run_brief, run_out

router = APIRouter(prefix="/guides", tags=["guides"])

Sort = Literal["useful", "popular", "new", "quick", "rating"]


@router.get("")
async def list_guides(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=200)] = None,
    category: Annotated[str | None, Query(max_length=32)] = None,
    difficulty: Annotated[int | None, Query(ge=1, le=3)] = None,
    verified: bool = False,
    max_minutes: Annotated[int | None, Query(ge=1, le=10000)] = None,
    author_id: int | None = None,
    sort: Sort = "useful",
    limit: Annotated[int, Query(ge=1, le=60)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GuideList:
    filters = {
        "category": category,
        "difficulty": difficulty,
        "verified": verified,
        "max_minutes": max_minutes,
        "author_id": author_id,
    }
    if q and q.strip():
        ids, snippets, modes = await search.hybrid_search(session, q, filters)
        page = ids[offset : offset + limit]
        rows = {g.id: g for g in await session.scalars(select(Guide).where(Guide.id.in_(page)))}
        guides = [rows[i] for i in page if i in rows]
        return GuideList(
            items=await cards_for(session, guides, snippets), total=len(ids), search_modes=modes
        )

    base = search._apply_filters(select(Guide), filters)
    order = {
        "useful": usefulness_sql().desc(),
        "popular": Guide.runs_count.desc(),
        "new": Guide.published_at.desc(),
        "quick": Guide.est_minutes.asc(),
        "rating": (Guide.rating_sum / func.greatest(Guide.rating_count, 1)).desc(),
    }[sort]
    total = await session.scalar(select(func.count()).select_from(base.subquery()))
    guides = list(await session.scalars(base.order_by(order, Guide.id).limit(limit).offset(offset)))
    return GuideList(items=await cards_for(session, guides), total=total or 0)


@router.get("/{slug}")
async def guide_detail(slug: str, session: SessionDep, viewer: ViewerDep) -> GuideDetail:
    g = await get_published_guide(session, slug)
    assert g.published_version_id is not None
    version = await get_version(session, g.published_version_id)
    card = (await cards_for(session, [g]))[0]

    stats: dict[str, StepPublicStats] = {s.key: StepPublicStats() for s in version.steps}
    votes = await session.execute(
        select(StepVote.step_key, StepVote.value, func.count())
        .where(StepVote.guide_id == g.id)
        .group_by(StepVote.step_key, StepVote.value)
    )
    for key, value, n in votes.all():
        if key in stats:
            if value > 0:
                stats[key].up += n
            else:
                stats[key].down += n
    comments = await session.execute(
        select(Comment.step_key, func.count())
        .where(Comment.guide_id == g.id, Comment.is_hidden.is_(False))
        .group_by(Comment.step_key)
    )
    for key, n in comments.all():
        if key in stats:
            stats[key].comments = n
    if viewer.key:
        mine = await session.execute(
            select(StepVote.step_key, StepVote.value).where(
                StepVote.version_id == version.id, StepVote.voter == viewer.key
            )
        )
        for key, value in mine.all():
            if key in stats:
                stats[key].my_vote = value

    run = await latest_run(session, g.id, viewer)
    my_rating = (
        await session.scalar(
            select(Rating.value).where(Rating.guide_id == g.id, Rating.voter == viewer.key)
        )
        if viewer.key
        else None
    )
    bookmarked = bool(
        viewer.user
        and await session.scalar(
            select(Bookmark.id).where(Bookmark.guide_id == g.id, Bookmark.user_id == viewer.user.id)
        )
    )
    verified_by = await session.get(User, g.verified_by_id) if g.verified_by_id else None
    versions_count = len(await list_versions(session, g.id))
    return GuideDetail(
        **card.model_dump(),
        version=version_brief(version),
        steps=[step_out(s) for s in version.steps],
        verified_by=user_brief(verified_by) if verified_by else None,
        verified_at=g.verified_at,
        step_stats=stats,
        my_run=await run_brief(session, run, g) if run else None,
        my_rating=my_rating,
        bookmarked=bookmarked,
        is_author=bool(viewer.user and viewer.user.id == g.author_id),
        versions_count=versions_count,
    )


@router.get("/{slug}/versions")
async def guide_versions(slug: str, session: SessionDep) -> list[VersionBrief]:
    g = await get_published_guide(session, slug)
    return await list_versions(session, g.id)


@router.get("/{slug}/forks")
async def guide_forks(slug: str, session: SessionDep) -> list[GuideCard]:
    g = await get_published_guide(session, slug)
    forks = await session.scalars(
        select(Guide)
        .where(Guide.forked_from_id == g.id, Guide.status == "published")
        .order_by(usefulness_sql().desc())
    )
    return await cards_for(session, list(forks))


@router.get("/{slug}/similar")
async def similar_guides(slug: str, session: SessionDep) -> list[GuideCard]:
    g = await get_published_guide(session, slug)
    if g.embedding is not None:
        stmt = (
            select(Guide)
            .where(Guide.status == "published", Guide.id != g.id, Guide.embedding.is_not(None))
            .order_by(Guide.embedding.cosine_distance(g.embedding))
            .limit(4)
        )
    else:
        stmt = (
            select(Guide)
            .where(Guide.status == "published", Guide.id != g.id, Guide.category == g.category)
            .order_by(usefulness_sql().desc())
            .limit(4)
        )
    return await cards_for(session, list(await session.scalars(stmt)))


def comment_out(c: Comment, author_id: int) -> CommentOut:
    return CommentOut(
        id=c.id,
        step_key=c.step_key,
        parent_id=c.parent_id,
        kind=c.kind,
        body=c.body,
        created_at=c.created_at,
        user=user_brief(c.user),
        is_author=c.user_id == author_id,
    )


@router.get("/{slug}/comments")
async def list_comments(
    slug: str, session: SessionDep, step_key: Annotated[str | None, Query(max_length=36)] = None
) -> list[CommentOut]:
    g = await get_published_guide(session, slug)
    stmt = (
        select(Comment)
        .where(Comment.guide_id == g.id, Comment.is_hidden.is_(False))
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at)
    )
    if step_key:
        stmt = stmt.where(Comment.step_key == step_key)
    return [comment_out(c, g.author_id) for c in await session.scalars(stmt)]


@router.post("/{slug}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    slug: str, body: CommentIn, session: SessionDep, user: CurrentUserDep
) -> CommentOut:
    g = await get_published_guide(session, slug)
    if body.parent_id:
        parent = await session.get(Comment, body.parent_id)
        if parent is None or parent.guide_id != g.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Комментарий не найден")
    c = Comment(
        guide_id=g.id,
        version_id=g.published_version_id,
        step_key=body.step_key,
        user_id=user.id,
        parent_id=body.parent_id,
        kind=body.kind,
        body=body.body,
    )
    session.add(c)
    await session.commit()
    c.user = user
    return comment_out(c, g.author_id)


@router.delete("/{slug}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    slug: str, comment_id: int, session: SessionDep, user: CurrentUserDep
) -> None:
    g = await get_published_guide(session, slug)
    c = await session.get(Comment, comment_id)
    if c is None or c.guide_id != g.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Комментарий не найден")
    if user.id not in (c.user_id, g.author_id) and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Нельзя удалить чужой комментарий")
    c.is_hidden = True
    await session.commit()


@router.post("/{slug}/votes")
async def vote_step(slug: str, body: VoteIn, session: SessionDep, viewer: ViewerDep) -> VoteOut:
    g = await get_published_guide(session, slug)
    voter = viewer.require_key()
    assert g.published_version_id is not None
    existing = await session.scalar(
        select(StepVote).where(
            StepVote.version_id == g.published_version_id,
            StepVote.step_key == body.step_key,
            StepVote.voter == voter,
        )
    )
    if body.value == 0:
        if existing:
            await session.delete(existing)
    elif existing:
        existing.value = body.value
    else:
        session.add(
            StepVote(
                guide_id=g.id,
                version_id=g.published_version_id,
                step_key=body.step_key,
                voter=voter,
                value=body.value,
            )
        )
    await session.flush()
    up, down = (
        await session.execute(
            select(
                func.count().filter(StepVote.value > 0), func.count().filter(StepVote.value < 0)
            ).where(StepVote.guide_id == g.id)
        )
    ).one()
    g.helpful_up, g.helpful_down = up, down
    step_up, step_down = (
        await session.execute(
            select(
                func.count().filter(StepVote.value > 0), func.count().filter(StepVote.value < 0)
            ).where(StepVote.guide_id == g.id, StepVote.step_key == body.step_key)
        )
    ).one()
    await session.commit()
    return VoteOut(step_key=body.step_key, up=step_up, down=step_down, my_vote=body.value or None)


@router.post("/{slug}/rating")
async def rate_guide(
    slug: str, body: RatingIn, session: SessionDep, viewer: ViewerDep
) -> RatingOut:
    g = await get_published_guide(session, slug)
    voter = viewer.require_key()
    r = await session.scalar(select(Rating).where(Rating.guide_id == g.id, Rating.voter == voter))
    if r:
        r.value, r.review = body.value, body.review
    else:
        session.add(
            Rating(
                guide_id=g.id,
                voter=voter,
                user_id=viewer.user.id if viewer.user else None,
                value=body.value,
                review=body.review,
            )
        )
    await session.flush()
    total, count = (
        await session.execute(
            select(func.coalesce(func.sum(Rating.value), 0), func.count()).where(
                Rating.guide_id == g.id
            )
        )
    ).one()
    g.rating_sum, g.rating_count = int(total), count
    await session.commit()
    return RatingOut(
        rating=round(total / count, 2) if count else None, rating_count=count, my_rating=body.value
    )


@router.post("/{slug}/bookmark")
async def toggle_bookmark(slug: str, session: SessionDep, user: CurrentUserDep) -> BookmarkOut:
    g = await get_published_guide(session, slug)
    b = await session.scalar(
        select(Bookmark).where(Bookmark.guide_id == g.id, Bookmark.user_id == user.id)
    )
    if b:
        await session.delete(b)
    else:
        session.add(Bookmark(guide_id=g.id, user_id=user.id))
    await session.commit()
    return BookmarkOut(bookmarked=b is None)


@router.post("/{slug}/fork", status_code=status.HTTP_201_CREATED)
async def fork(slug: str, session: SessionDep, user: CurrentUserDep) -> CreatedOut:
    g = await get_published_guide(session, slug)
    copy = await fork_guide(session, g, user)
    await session.commit()
    return CreatedOut(id=copy.id, slug=copy.slug)


@router.post("/{slug}/suggestions", status_code=status.HTTP_201_CREATED)
async def suggest_edit(
    slug: str, body: SuggestionIn, session: SessionDep, user: CurrentUserDep
) -> CreatedOut:
    g = await get_published_guide(session, slug)
    assert g.published_version_id is not None
    v = await get_version(session, g.published_version_id)
    if body.step_key not in {s.key for s in v.steps}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Шаг не найден")
    if g.author_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Свою инструкцию правьте в редакторе")
    s = Suggestion(
        guide_id=g.id,
        base_version_id=v.id,
        step_key=body.step_key,
        user_id=user.id,
        title=body.title or None,
        body=body.body,
        message=body.message,
    )
    session.add(s)
    await session.commit()
    return CreatedOut(id=s.id, slug=g.slug)


@router.post("/{slug}/runs")
async def start_run(
    slug: str, session: SessionDep, viewer: ViewerDep, restart: bool = False
) -> RunOut:
    g = await get_published_guide(session, slug)
    viewer.require_key()
    run = await latest_run(session, g.id, viewer)
    if run is None or restart:
        run = new_run(g, viewer)
        session.add(run)
        g.runs_count += 1
        await session.commit()
    return await run_out(session, run, g)
