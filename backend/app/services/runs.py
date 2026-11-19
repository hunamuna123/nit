import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Viewer
from app.models import Guide, GuideVersion, Run
from app.schemas import RunBrief, RunOut, RunState
from app.services.guides import get_version, step_out


def viewer_filter(viewer: Viewer):  # noqa: ANN201
    if viewer.user and viewer.anon_id:
        return or_(Run.user_id == viewer.user.id, Run.anon_id == viewer.anon_id)
    if viewer.user:
        return Run.user_id == viewer.user.id
    return Run.anon_id == viewer.anon_id


async def latest_run(session: AsyncSession, guide_id: int, viewer: Viewer) -> Run | None:
    if viewer.key is None:
        return None
    return await session.scalar(
        select(Run)
        .where(Run.guide_id == guide_id, viewer_filter(viewer))
        .order_by(Run.last_activity_at.desc())
        .limit(1)
    )


def _state(run: Run) -> RunState:
    return RunState.model_validate(run.state or {})


async def run_brief(session: AsyncSession, run: Run, g: Guide) -> RunBrief:
    v = await session.get(GuideVersion, run.version_id)
    steps_total = await _steps_total(session, run.version_id)
    done = len(_state(run).done)
    return RunBrief(
        id=run.id,
        status=run.status,
        current_step=run.current_step,
        progress=1.0
        if run.status == "completed"
        else round(done / steps_total, 3)
        if steps_total
        else 0.0,
        version_number=v.number if v else 0,
        outdated=run.version_id != g.published_version_id,
    )


async def _steps_total(session: AsyncSession, version_id: int) -> int:
    v = await get_version(session, version_id)
    return len(v.steps)


async def run_out(session: AsyncSession, run: Run, g: Guide) -> RunOut:
    v = await get_version(session, run.version_id)
    return RunOut(
        id=run.id,
        guide_id=g.id,
        guide_slug=g.slug,
        version_id=v.id,
        version_number=v.number,
        status=run.status,
        current_step=run.current_step,
        state=_state(run),
        started_at=run.started_at,
        completed_at=run.completed_at,
        outdated=run.version_id != g.published_version_id,
        steps=[step_out(s) for s in v.steps],
        title=v.title,
    )


def new_run(g: Guide, viewer: Viewer) -> Run:
    assert g.published_version_id is not None
    return Run(
        id=str(uuid.uuid4()),
        guide_id=g.id,
        version_id=g.published_version_id,
        user_id=viewer.user.id if viewer.user else None,
        anon_id=None if viewer.user else viewer.anon_id,
        state={"checked": {}, "done": []},
    )
