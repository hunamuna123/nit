# индекс проблемности шага 0-100, короче из 4 штук:
# 50% бросили на шаге из дошедших, 20% медиана времени vs заявленное,
# 15% не полезно, 15% жмут застрял. >=45 все плохо, >=25 так себе

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from statistics import median
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import utcnow
from app.models import Comment, Guide, GuideVersion, Run, Step, StepEvent, StepVote, Suggestion
from app.schemas import (
    Analytics,
    AnalyticsTotals,
    DayPoint,
    HotStep,
    StepAnalytics,
    VersionStat,
)
from app.services.guides import get_version, version_brief


@dataclass
class _Funnel:
    reached: Counter[str] = field(default_factory=Counter)
    completed: Counter[str] = field(default_factory=Counter)
    dropped: Counter[str] = field(default_factory=Counter)
    stuck: Counter[str] = field(default_factory=Counter)
    durations: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    runs: int = 0
    finished: int = 0
    abandoned: int = 0
    active: int = 0
    total_minutes: list[float] = field(default_factory=list)
    learners: set[str] = field(default_factory=set)


def _is_abandoned(run: Run, now: datetime) -> bool:
    limit = timedelta(minutes=get_settings().abandon_after_minutes)
    return run.status != "completed" and run.last_activity_at < now - limit


async def _funnel(session: AsyncSession, version_id: int, steps: list[Step]) -> _Funnel:
    now = utcnow()
    pos = {s.key: s.position for s in steps}
    key_at = {s.position: s.key for s in steps}
    runs = list(await session.scalars(select(Run).where(Run.version_id == version_id)))
    events = (
        await session.execute(
            select(
                StepEvent.run_id, StepEvent.step_key, StepEvent.type, StepEvent.duration_ms
            ).where(StepEvent.version_id == version_id)
        )
    ).all()

    furthest: dict[str, int] = {}
    completed_by_run: dict[str, set[str]] = defaultdict(set)
    f = _Funnel()
    for run_id, key, kind, duration in events:
        if key not in pos:
            continue
        if kind in ("view", "complete"):
            furthest[run_id] = max(furthest.get(run_id, 0), pos[key])
        if kind == "complete":
            completed_by_run[run_id].add(key)
            if duration:
                f.durations[key].append(duration)
        elif kind == "stuck":
            f.stuck[key] += 1

    for run in runs:
        f.runs += 1
        f.learners.add(f"u{run.user_id}" if run.user_id else f"a{run.anon_id}")
        top = max(furthest.get(run.id, 0), min(run.current_step, len(steps) - 1))
        for p in range(top + 1):
            f.reached[key_at[p]] += 1
        for key in completed_by_run.get(run.id, ()):
            f.completed[key] += 1
        if run.status == "completed":
            f.finished += 1
            if run.completed_at:
                f.total_minutes.append((run.completed_at - run.started_at).total_seconds() / 60)
        elif _is_abandoned(run, now):
            f.abandoned += 1
            if steps:
                f.dropped[key_at[top]] += 1
        else:
            f.active += 1
    return f


def _times(n: int) -> str:
    a, b = n % 100, n % 10
    word = "раз" if 11 <= a <= 14 or b not in (2, 3, 4) else "раза"
    return f"{n} {word}"


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _score(
    reached: int, dropped: int, ratio: float | None, up: int, down: int, stuck: int
) -> tuple[int, list[str]]:
    if reached == 0:
        return 0, []
    drop_rate = dropped / reached
    s_drop = _clamp(drop_rate / 0.3)
    s_time = _clamp(((ratio or 1.0) - 1.0) / 2.0)
    down_share = down / (up + down + 2)
    s_vote = _clamp((down_share - 0.15) / 0.45)
    stuck_rate = stuck / reached
    s_stuck = _clamp(stuck_rate / 0.25)
    score = round(100 * (0.5 * s_drop + 0.2 * s_time + 0.15 * s_vote + 0.15 * s_stuck))

    reasons: list[str] = []
    if drop_rate >= 0.08 and dropped >= 2:
        reasons.append(f"Бросают {round(drop_rate * 100)}% дошедших")
    if ratio and ratio >= 1.6:
        reasons.append(f"В {ratio:.1f} раза дольше заявленного")
    if down >= 3 and down / (up + down) >= 0.35:
        reasons.append(f"{round(down / (up + down) * 100)}% считают шаг бесполезным")
    if stuck >= 2:
        reasons.append(f"«Застрял» нажимали {_times(stuck)}")
    return score, reasons


def _level(score: int) -> str:
    return "critical" if score >= 45 else "warn" if score >= 25 else "ok"


async def compute(session: AsyncSession, g: Guide, version_id: int | None = None) -> Analytics:
    vid = version_id or g.published_version_id or g.draft_version_id
    assert vid is not None
    version = await get_version(session, vid)
    steps = list(version.steps)
    f = await _funnel(session, vid, steps)

    prev_drop: dict[str, float] = {}
    if version.number > 1:
        prev = await session.scalar(
            select(GuideVersion).where(
                GuideVersion.guide_id == g.id, GuideVersion.number == version.number - 1
            )
        )
        if prev:
            prev_v = await get_version(session, prev.id)
            pf = await _funnel(session, prev.id, list(prev_v.steps))
            prev_drop = {k: pf.dropped[k] / n for k, n in pf.reached.items() if n}

    votes = (
        await session.execute(
            select(StepVote.step_key, StepVote.value, func.count())
            .where(StepVote.version_id == vid)
            .group_by(StepVote.step_key, StepVote.value)
        )
    ).all()
    up: Counter[str] = Counter()
    down: Counter[str] = Counter()
    for key, value, n in votes:
        (up if value > 0 else down)[key] += n

    comments = dict(
        (
            await session.execute(
                select(Comment.step_key, func.count())
                .where(Comment.guide_id == g.id, Comment.step_key.is_not(None))
                .group_by(Comment.step_key)
            )
        ).all()
    )
    suggestions = dict(
        (
            await session.execute(
                select(Suggestion.step_key, func.count())
                .where(Suggestion.guide_id == g.id, Suggestion.status == "open")
                .group_by(Suggestion.step_key)
            )
        ).all()
    )

    out_steps: list[StepAnalytics] = []
    for s in steps:
        reached = f.reached[s.key]
        dropped = f.dropped[s.key]
        durations = f.durations.get(s.key) or []
        med = median(durations) / 1000 if durations else None
        ratio = round(med / (s.minutes * 60), 2) if med and s.minutes else None
        score, reasons = _score(reached, dropped, ratio, up[s.key], down[s.key], f.stuck[s.key])
        out_steps.append(
            StepAnalytics(
                key=s.key,
                position=s.position,
                title=s.title,
                minutes=s.minutes,
                reached=reached,
                completed=f.completed[s.key],
                dropped=dropped,
                drop_rate=round(dropped / reached, 3) if reached else 0.0,
                median_seconds=round(med, 1) if med else None,
                time_ratio=ratio,
                up=up[s.key],
                down=down[s.key],
                stuck=f.stuck[s.key],
                comments=comments.get(s.key, 0),
                suggestions=suggestions.get(s.key, 0),
                score=score,
                level=_level(score),  # type: ignore[arg-type]
                reasons=reasons,
                prev_drop_rate=round(prev_drop[s.key], 3) if s.key in prev_drop else None,
            )
        )

    total_up, total_down = sum(up.values()), sum(down.values())
    totals = AnalyticsTotals(
        runs=f.runs,
        completed=f.finished,
        active=f.active,
        abandoned=f.abandoned,
        completion_rate=round(f.finished / f.runs, 3) if f.runs else 0.0,
        median_total_minutes=round(median(f.total_minutes), 1) if f.total_minutes else None,
        learners=len(f.learners),
        rating=round(g.rating_sum / g.rating_count, 2) if g.rating_count else None,
        rating_count=g.rating_count,
        helpful_ratio=round(total_up / (total_up + total_down), 3)
        if total_up + total_down
        else None,
    )

    bottlenecks = [
        s.key for s in sorted(out_steps, key=lambda s: s.score, reverse=True) if s.level != "ok"
    ][:3]

    return Analytics(
        guide_id=g.id,
        title=g.title,
        slug=g.slug,
        version=version_brief(version),
        totals=totals,
        steps=out_steps,
        timeline=await _timeline(session, g.id),
        versions=await _versions(session, g.id),
        bottlenecks=bottlenecks,
    )


async def _timeline(session: AsyncSession, guide_id: int, days: int = 30) -> list[DayPoint]:
    since = (utcnow() - timedelta(days=days - 1)).date()
    started = dict(
        (
            await session.execute(
                select(func.date(Run.started_at), func.count())
                .where(Run.guide_id == guide_id, func.date(Run.started_at) >= since)
                .group_by(func.date(Run.started_at))
            )
        ).all()
    )
    completed = dict(
        (
            await session.execute(
                select(func.date(Run.completed_at), func.count())
                .where(
                    Run.guide_id == guide_id,
                    Run.completed_at.is_not(None),
                    func.date(Run.completed_at) >= since,
                )
                .group_by(func.date(Run.completed_at))
            )
        ).all()
    )
    return [
        DayPoint(
            day=since + timedelta(days=i),
            started=started.get(since + timedelta(days=i), 0),
            completed=completed.get(since + timedelta(days=i), 0),
        )
        for i in range(days)
    ]


async def _versions(session: AsyncSession, guide_id: int) -> list[VersionStat]:
    rows = (
        await session.execute(
            select(
                GuideVersion,
                func.count(Run.id),
                func.count(Run.id).filter(Run.status == "completed"),
            )
            .outerjoin(Run, Run.version_id == GuideVersion.id)
            .where(GuideVersion.guide_id == guide_id, GuideVersion.is_draft.is_(False))
            .group_by(GuideVersion.id)
            .order_by(GuideVersion.number)
        )
    ).all()
    return [
        VersionStat(
            id=v.id,
            number=v.number,
            published_at=v.published_at,
            changelog=v.changelog,
            runs=runs,
            completion_rate=round(done / runs, 3) if runs else 0.0,
        )
        for v, runs, done in rows
    ]


async def hot_step(session: AsyncSession, g: Guide) -> HotStep | None:
    if g.published_version_id is None:
        return None
    a = await compute(session, g)
    if not a.bottlenecks:
        return None
    s = next(s for s in a.steps if s.key == a.bottlenecks[0])
    return HotStep(key=s.key, title=s.title, score=s.score, level=s.level)


def problem_context(a: Analytics) -> list[dict[str, Any]]:
    return [
        {"key": s.key, "number": s.position + 1, "title": s.title, "reasons": s.reasons}
        for s in a.steps
        if s.key in a.bottlenecks
    ]
