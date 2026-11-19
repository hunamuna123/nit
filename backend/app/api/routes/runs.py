import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep, Viewer, ViewerDep
from app.api.routes.guides import comment_out
from app.db import utcnow
from app.models import Comment, Guide, Run, StepEvent
from app.schemas import HelpIn, HelpOut, RunOut, RunSyncIn
from app.services import ai
from app.services.guides import get_version
from app.services.runs import run_out

router = APIRouter(prefix="/runs", tags=["runs"])


async def _own_run(session: SessionDep, run_id: str, viewer: Viewer) -> tuple[Run, Guide]:
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Прохождение не найдено")
    mine = (viewer.user is not None and run.user_id == viewer.user.id) or (
        viewer.anon_id is not None and run.anon_id == viewer.anon_id
    )
    if not mine:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Это не ваше прохождение")
    g = await session.get(Guide, run.guide_id)
    assert g is not None
    return run, g


@router.get("/{run_id}")
async def get_run(run_id: str, session: SessionDep, viewer: ViewerDep) -> RunOut:
    run, g = await _own_run(session, run_id, viewer)
    return await run_out(session, run, g)


@router.post("/{run_id}/sync")
async def sync_run(run_id: str, body: RunSyncIn, session: SessionDep, viewer: ViewerDep) -> RunOut:
    run, g = await _own_run(session, run_id, viewer)
    version = await get_version(session, run.version_id)
    steps = {s.key: s for s in version.steps}
    now = utcnow()

    checked: dict[str, list[str]] = {}
    for key, items in body.state.checked.items():
        if key in steps:
            valid = {i["key"] for i in steps[key].checklist}
            checked[key] = [i for i in dict.fromkeys(items) if i in valid]
    done = [k for k in dict.fromkeys(body.state.done) if k in steps]
    run.state = {"checked": checked, "done": done}
    run.current_step = min(body.current_step, max(0, len(steps) - 1))
    run.last_activity_at = now

    # по client_id, чтоб офлайн очередь не задваивала
    rows = []
    floor = run.started_at - timedelta(days=1)
    for e in body.events:
        if e.step_key not in steps:
            continue
        at = e.at if e.at and floor < e.at <= now else now
        rows.append(
            {
                "run_id": run.id,
                "guide_id": g.id,
                "version_id": run.version_id,
                "step_key": e.step_key,
                "type": e.type,
                "duration_ms": e.duration_ms,
                "client_id": f"{run.id[:8]}:{e.client_id}",
                "created_at": at,
            }
        )
    if rows:
        await session.execute(
            insert(StepEvent).values(rows).on_conflict_do_nothing(index_elements=["client_id"])
        )

    if body.completed and run.status != "completed":
        run.status = "completed"
        run.completed_at = now
        g.completions_count += 1
    elif not body.completed and run.status == "completed" and len(done) < len(steps):
        run.status = "active"
        run.completed_at = None
        g.completions_count = max(0, g.completions_count - 1)
    await session.commit()
    return await run_out(session, run, g)


@router.post("/{run_id}/help")
async def stuck_help(run_id: str, body: HelpIn, session: SessionDep, viewer: ViewerDep) -> HelpOut:
    run, g = await _own_run(session, run_id, viewer)
    version = await get_version(session, run.version_id)
    step = next((s for s in version.steps if s.key == body.step_key), None)
    if step is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Шаг не найден")

    session.add(
        StepEvent(
            run_id=run.id,
            guide_id=g.id,
            version_id=run.version_id,
            step_key=step.key,
            type="stuck",
            client_id=f"srv:{uuid.uuid4()}",
        )
    )
    await session.commit()

    priority = case((Comment.kind == "tip", 0), (Comment.kind == "question", 2), else_=1)
    comments = list(
        await session.scalars(
            select(Comment)
            .where(
                Comment.guide_id == g.id,
                Comment.step_key == step.key,
                Comment.is_hidden.is_(False),
            )
            .options(selectinload(Comment.user))
            .order_by(priority, Comment.created_at.desc())
            .limit(6)
        )
    )
    hint: str | None = None
    try:
        hint = await ai.stuck_hint(
            session,
            viewer.user,
            version.title,
            {
                "title": step.title,
                "body": step.body,
                "checklist": [i["text"] for i in step.checklist],
            },
            body.question,
            [c.body for c in comments],
        )
    except HTTPException:
        hint = None
    return HelpOut(
        hint=hint, tips=[comment_out(c, g.author_id) for c in comments], ai=hint is not None
    )
