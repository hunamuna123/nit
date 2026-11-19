from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, SessionDep
from app.db import SessionLocal, utcnow
from app.models import Comment, Guide, GuideVersion, Step, Suggestion
from app.schemas import (
    Analytics,
    CreatedOut,
    CreateGuideIn,
    EditorDoc,
    EditorDocIn,
    InsightItem,
    InsightsOut,
    PublishIn,
    StudioGuideItem,
    SuggestionOut,
    SuggestionResolveIn,
    VersionBrief,
)
from app.services import ai, analytics
from app.services.guides import (
    cards_for,
    create_guide,
    doc_from_draft,
    editor_doc,
    embedding_text,
    get_own_guide,
    get_version,
    new_key,
    publish,
    save_draft,
    user_brief,
    version_brief,
)

router = APIRouter(prefix="/studio", tags=["studio"])


async def reindex_embedding(guide_id: int) -> None:
    async with SessionLocal() as session:
        g = await session.get(Guide, guide_id)
        if g is None or g.published_version_id is None:
            return
        v = await get_version(session, g.published_version_id)
        vectors = await ai.embed([embedding_text(g, v.steps)])
        if vectors:
            g.embedding = vectors[0]
            await session.commit()


@router.get("/guides")
async def my_guides(session: SessionDep, user: CurrentUserDep) -> list[StudioGuideItem]:
    guides = list(
        await session.scalars(
            select(Guide)
            .where(Guide.author_id == user.id, Guide.status != "archived")
            .order_by(Guide.updated_at.desc())
        )
    )
    cards = await cards_for(session, guides)
    open_counts = dict(
        (
            await session.execute(
                select(Suggestion.guide_id, func.count())
                .where(Suggestion.status == "open", Suggestion.guide_id.in_([g.id for g in guides]))
                .group_by(Suggestion.guide_id)
            )
        ).all()
    )
    out = []
    for g, card in zip(guides, cards, strict=True):
        doc = await editor_doc(session, g)
        out.append(
            StudioGuideItem(
                **card.model_dump(),
                status=g.status,
                has_unpublished_changes=doc.has_unpublished_changes,
                open_suggestions=open_counts.get(g.id, 0),
                hot_step=await analytics.hot_step(session, g),
                updated_at=g.updated_at,
            )
        )
    return out


@router.post("/guides", status_code=status.HTTP_201_CREATED)
async def new_guide(body: CreateGuideIn, session: SessionDep, user: CurrentUserDep) -> CreatedOut:
    doc = (
        doc_from_draft(body.draft)
        if body.draft
        else EditorDocIn(title=body.title or "Новая инструкция")
    )
    g = await create_guide(session, user, doc)
    await session.commit()
    return CreatedOut(id=g.id, slug=g.slug)


@router.get("/guides/{guide_id}")
async def get_doc(guide_id: int, session: SessionDep, user: CurrentUserDep) -> EditorDoc:
    g = await get_own_guide(session, guide_id, user)
    return await editor_doc(session, g)


@router.put("/guides/{guide_id}")
async def save_doc(
    guide_id: int, body: EditorDocIn, session: SessionDep, user: CurrentUserDep
) -> EditorDoc:
    g = await get_own_guide(session, guide_id, user)
    await save_draft(session, g, body)
    await session.commit()
    return await editor_doc(session, g)


@router.post("/guides/{guide_id}/publish")
async def publish_doc(
    guide_id: int,
    body: PublishIn,
    session: SessionDep,
    user: CurrentUserDep,
    background: BackgroundTasks,
) -> EditorDoc:
    g = await get_own_guide(session, guide_id, user)
    await publish(session, g, body.changelog)
    await session.commit()
    background.add_task(reindex_embedding, g.id)
    return await editor_doc(session, g)


@router.post("/guides/{guide_id}/discard")
async def discard_changes(guide_id: int, session: SessionDep, user: CurrentUserDep) -> EditorDoc:
    g = await get_own_guide(session, guide_id, user)
    if g.published_version_id is None or g.draft_version_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нет опубликованной версии")
    pub = await get_version(session, g.published_version_id)
    draft = await get_version(session, g.draft_version_id)
    draft.title, draft.summary = pub.title, pub.summary
    draft.steps = [
        Step(
            key=s.key,
            position=s.position,
            title=s.title,
            body=s.body,
            minutes=s.minutes,
            checklist=list(s.checklist),
        )
        for s in pub.steps
    ]
    await session.commit()
    return await editor_doc(session, g)


@router.delete("/guides/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_guide(guide_id: int, session: SessionDep, user: CurrentUserDep) -> None:
    g = await get_own_guide(session, guide_id, user)
    if g.runs_count == 0 and g.published_version_id is None:
        await session.delete(g)
    else:
        g.status = "archived"
    await session.commit()


@router.get("/guides/{guide_id}/versions")
async def doc_versions(
    guide_id: int, session: SessionDep, user: CurrentUserDep
) -> list[VersionBrief]:
    g = await get_own_guide(session, guide_id, user)
    rows = await session.scalars(
        select(GuideVersion)
        .where(GuideVersion.guide_id == g.id, GuideVersion.is_draft.is_(False))
        .options(selectinload(GuideVersion.steps))
        .order_by(GuideVersion.number.desc())
    )
    return [version_brief(v) for v in rows]


@router.get("/guides/{guide_id}/analytics")
async def guide_analytics(
    guide_id: int, session: SessionDep, user: CurrentUserDep, version_id: int | None = None
) -> Analytics:
    g = await get_own_guide(session, guide_id, user)
    if g.published_version_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Инструкция ещё не опубликована")
    if version_id is not None:
        v = await session.get(GuideVersion, version_id)
        if v is None or v.guide_id != g.id or v.is_draft:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Версия не найдена")
    return await analytics.compute(session, g, version_id)


@router.post("/guides/{guide_id}/insights")
async def guide_insights(guide_id: int, session: SessionDep, user: CurrentUserDep) -> InsightsOut:
    g = await get_own_guide(session, guide_id, user)
    if g.published_version_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Инструкция ещё не опубликована")
    a = await analytics.compute(session, g)
    problems = analytics.problem_context(a)
    if not problems:
        return InsightsOut(
            summary="Явных узких мест не найдено — ученики проходят ровно.", items=[]
        )
    for p in problems:
        p["comments"] = list(
            await session.scalars(
                select(Comment.body)
                .where(Comment.guide_id == g.id, Comment.step_key == p["key"])
                .order_by(Comment.created_at.desc())
                .limit(12)
            )
        )
    v = await get_version(session, g.published_version_id)
    steps = [
        {"title": s.title, "body": s.body, "checklist": [i["text"] for i in s.checklist]}
        for s in v.steps
    ]
    result = await ai.bottleneck_insights(session, user, g.title, steps, problems)
    by_number = {p["number"]: p for p in problems}
    items = []
    for it in result.items:
        p = by_number.get(it.step_number)
        if p is None:
            continue
        items.append(
            InsightItem(
                step_key=p["key"],
                step_title=p["title"],
                diagnosis=it.diagnosis,
                recommendation=it.recommendation,
                proposed_title=it.proposed_title,
                proposed_body=it.proposed_body,
                proposed_checklist=it.proposed_checklist[:6],
            )
        )
    return InsightsOut(summary=result.summary, items=items)


async def suggestion_out(session: SessionDep, s: Suggestion, g: Guide) -> SuggestionOut:
    current = None
    if g.draft_version_id:
        current = await session.scalar(
            select(Step).where(Step.version_id == g.draft_version_id, Step.key == s.step_key)
        )
    return SuggestionOut(
        id=s.id,
        guide_id=g.id,
        guide_slug=g.slug,
        guide_title=g.title,
        step_key=s.step_key,
        current_title=current.title if current else None,
        current_body=current.body if current else None,
        title=s.title,
        body=s.body,
        message=s.message,
        status=s.status,
        reply=s.reply,
        created_at=s.created_at,
        resolved_at=s.resolved_at,
        user=user_brief(s.user),
    )


@router.get("/suggestions")
async def inbox(
    session: SessionDep,
    user: CurrentUserDep,
    status_: Annotated[
        Literal["open", "accepted", "rejected", "all"], Query(alias="status")
    ] = "open",
) -> list[SuggestionOut]:
    stmt = (
        select(Suggestion, Guide)
        .join(Guide, Guide.id == Suggestion.guide_id)
        .where(Guide.author_id == user.id)
        .options(selectinload(Suggestion.user))
        .order_by(Suggestion.created_at.desc())
    )
    if status_ != "all":
        stmt = stmt.where(Suggestion.status == status_)
    rows = (await session.execute(stmt)).all()
    return [await suggestion_out(session, s, g) for s, g in rows]


async def _own_suggestion(
    session: SessionDep, suggestion_id: int, user: CurrentUserDep
) -> tuple[Suggestion, Guide]:
    s = await session.scalar(
        select(Suggestion)
        .where(Suggestion.id == suggestion_id)
        .options(selectinload(Suggestion.user))
    )
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Предложение не найдено")
    g = await get_own_guide(session, s.guide_id, user)
    if s.status != "open":
        raise HTTPException(status.HTTP_409_CONFLICT, "Предложение уже рассмотрено")
    return s, g


@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(
    suggestion_id: int, body: SuggestionResolveIn, session: SessionDep, user: CurrentUserDep
) -> SuggestionOut:
    s, g = await _own_suggestion(session, suggestion_id, user)
    assert g.draft_version_id is not None
    draft = await get_version(session, g.draft_version_id)
    step = next((x for x in draft.steps if x.key == s.step_key), None)
    if step is None:
        # шаг выпилили из черновика, кидаем в конец
        step = Step(
            key=s.step_key or new_key(),
            position=len(draft.steps),
            title=s.title or "Шаг",
            body="",
            minutes=5,
            checklist=[],
        )
        draft.steps.append(step)
    step.body = s.body
    if s.title:
        step.title = s.title
    draft.updated_at = utcnow()
    s.status, s.reply, s.resolved_at = "accepted", body.reply, utcnow()
    await session.commit()
    return await suggestion_out(session, s, g)


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: int, body: SuggestionResolveIn, session: SessionDep, user: CurrentUserDep
) -> SuggestionOut:
    s, g = await _own_suggestion(session, suggestion_id, user)
    s.status, s.reply, s.resolved_at = "rejected", body.reply, utcnow()
    await session.commit()
    return await suggestion_out(session, s, g)
