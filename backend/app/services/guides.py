import re
import secrets
import uuid
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Float, Integer, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.catalog import CATEGORY_SLUGS, COVERS
from app.db import utcnow
from app.models import Guide, GuideVersion, Step, Suggestion, User
from app.schemas import (
    ChecklistItem,
    EditorDoc,
    EditorDocIn,
    ForkRef,
    GuideCard,
    GuideDraft,
    StepOut,
    UserBrief,
    VersionBrief,
)

_TRANSLIT = dict(
    zip(
        "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
        [
            "a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p",
            "r", "s", "t", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya",
        ],
        strict=True,
    )
)  # fmt: skip


def new_key() -> str:
    return str(uuid.uuid4())


def slugify(title: str) -> str:
    base = "".join(_TRANSLIT.get(ch, ch) for ch in title.lower())
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:60].strip("-") or "guide"
    return f"{base}-{secrets.token_hex(2)}"


def usefulness_value(g: Guide) -> int:
    rating = (g.rating_sum + 14.0) / (g.rating_count + 4) / 5
    completion = (g.completions_count + 2.0) / (g.runs_count + 4)
    helpful = (g.helpful_up + 1.0) / (g.helpful_up + g.helpful_down + 2)
    score = 100 * (0.45 * rating + 0.35 * completion + 0.2 * helpful)
    if g.verified_version_id:
        score += 4
    return round(min(100.0, score))


def usefulness_sql() -> Any:
    g = Guide
    rating = (cast(g.rating_sum, Float) + 14.0) / (g.rating_count + 4) / 5
    completion = (cast(g.completions_count, Float) + 2.0) / (g.runs_count + 4)
    helpful = (cast(g.helpful_up, Float) + 1.0) / (g.helpful_up + g.helpful_down + 2)
    verified = cast(g.verified_version_id.is_not(None), Integer) * 4
    return 100 * (0.45 * rating + 0.35 * completion + 0.2 * helpful) + verified


def user_brief(u: User) -> UserBrief:
    return UserBrief(id=u.id, name=u.name, role=u.role, expert_categories=u.expert_categories)  # type: ignore[arg-type]


def step_out(s: Step) -> StepOut:
    return StepOut(
        key=s.key,
        position=s.position,
        title=s.title,
        body=s.body,
        minutes=s.minutes,
        checklist=[ChecklistItem(key=i["key"], text=i["text"]) for i in s.checklist],
    )


def version_brief(v: GuideVersion, steps_count: int | None = None) -> VersionBrief:
    return VersionBrief(
        id=v.id,
        number=v.number,
        changelog=v.changelog,
        published_at=v.published_at,
        steps_count=steps_count if steps_count is not None else len(v.steps),
    )


def guide_card(
    g: Guide,
    author: User,
    forked_from: Guide | None = None,
    forked_author: User | None = None,
    snippet: str | None = None,
) -> GuideCard:
    fork = None
    if forked_from is not None:
        fork = ForkRef(
            id=forked_from.id,
            slug=forked_from.slug,
            title=forked_from.title,
            author_name=forked_author.name if forked_author else "",
        )
    return GuideCard(
        id=g.id,
        slug=g.slug,
        title=g.title,
        summary=g.summary,
        category=g.category,
        tags=g.tags,
        difficulty=g.difficulty,
        cover=g.cover,
        est_minutes=g.est_minutes,
        steps_count=g.steps_count,
        author=user_brief(author),
        runs_count=g.runs_count,
        completions_count=g.completions_count,
        completion_rate=round(g.completions_count / g.runs_count, 3) if g.runs_count else 0.0,
        rating=round(g.rating_sum / g.rating_count, 2) if g.rating_count else None,
        rating_count=g.rating_count,
        usefulness=usefulness_value(g),
        verified=g.verified_version_id is not None,
        forked_from=fork,
        forks_count=g.forks_count,
        published_at=g.published_at,
        snippet=snippet,
    )


async def cards_for(
    session: AsyncSession, guides: Sequence[Guide], snippets: dict[int, str] | None = None
) -> list[GuideCard]:
    if not guides:
        return []
    fork_ids = {g.forked_from_id for g in guides if g.forked_from_id}
    forks: dict[int, Guide] = {}
    if fork_ids:
        rows = await session.scalars(select(Guide).where(Guide.id.in_(fork_ids)))
        forks = {g.id: g for g in rows}
    user_ids = {g.author_id for g in guides} | {f.author_id for f in forks.values()}
    users = {u.id: u for u in await session.scalars(select(User).where(User.id.in_(user_ids)))}
    out = []
    for g in guides:
        src = forks.get(g.forked_from_id) if g.forked_from_id else None
        out.append(
            guide_card(
                g,
                users[g.author_id],
                src,
                users.get(src.author_id) if src else None,
                (snippets or {}).get(g.id),
            )
        )
    return out


async def get_version(session: AsyncSession, version_id: int) -> GuideVersion:
    v = await session.scalar(
        select(GuideVersion)
        .where(GuideVersion.id == version_id)
        .options(selectinload(GuideVersion.steps))
    )
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Версия не найдена")
    return v


async def get_published_guide(session: AsyncSession, slug: str) -> Guide:
    g = await session.scalar(select(Guide).where(Guide.slug == slug))
    if g is None or g.status != "published" or g.published_version_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Инструкция не найдена")
    return g


async def get_own_guide(session: AsyncSession, guide_id: int, user: User) -> Guide:
    g = await session.get(Guide, guide_id)
    if g is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Инструкция не найдена")
    if g.author_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Это не ваша инструкция")
    return g


async def list_versions(session: AsyncSession, guide_id: int) -> list[VersionBrief]:
    counts = select(Step.version_id, func.count().label("n")).group_by(Step.version_id).subquery()
    rows = await session.execute(
        select(GuideVersion, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.version_id == GuideVersion.id)
        .where(GuideVersion.guide_id == guide_id, GuideVersion.is_draft.is_(False))
        .order_by(GuideVersion.number.desc())
    )
    return [version_brief(v, n) for v, n in rows.all()]


def _clean_doc(doc: EditorDocIn) -> EditorDocIn:
    if doc.category not in CATEGORY_SLUGS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Неизвестная категория")
    doc.tags = list(dict.fromkeys(t.lower() for t in doc.tags))[:8]
    return doc


def _build_steps(doc: EditorDocIn) -> list[Step]:
    steps: list[Step] = []
    seen: set[str] = set()
    for i, s in enumerate(doc.steps):
        key = s.key if s.key and s.key not in seen else new_key()
        seen.add(key)
        items, item_seen = [], set()
        for it in s.checklist:
            ik = it.key if it.key and it.key not in item_seen else new_key()[:8]
            item_seen.add(ik)
            items.append({"key": ik, "text": it.text})
        steps.append(
            Step(
                key=key,
                position=i,
                title=s.title or f"Шаг {i + 1}",
                body=s.body,
                minutes=s.minutes,
                checklist=items,
            )
        )
    return steps


def doc_from_draft(d: GuideDraft) -> EditorDocIn:
    from app.schemas import ChecklistItemIn, StepIn

    return EditorDocIn(
        title=d.title[:160],
        summary=d.summary[:600],
        category=d.category if d.category in CATEGORY_SLUGS else "study",
        tags=[t[:40] for t in d.tags if t][:8],
        difficulty=min(3, max(1, d.difficulty)),
        cover=COVERS[secrets.randbelow(len(COVERS))],  # type: ignore[arg-type]
        steps=[
            StepIn(
                title=s.title[:200],
                body=s.body[:20000],
                minutes=min(600, max(1, s.minutes)),
                checklist=[ChecklistItemIn(text=c[:300]) for c in s.checklist if c][:12],
            )
            for s in d.steps[:40]
        ],
    )


async def create_guide(session: AsyncSession, author: User, doc: EditorDocIn) -> Guide:
    doc = _clean_doc(doc)
    g = Guide(
        slug=slugify(doc.title or "instrukciya"),
        author_id=author.id,
        category=doc.category,
        tags=doc.tags,
        difficulty=doc.difficulty,
        cover=doc.cover,
        status="draft",
        title=doc.title,
        summary=doc.summary,
    )
    session.add(g)
    await session.flush()
    draft = GuideVersion(
        guide_id=g.id, number=0, is_draft=True, title=doc.title, summary=doc.summary
    )
    draft.steps = _build_steps(doc)
    session.add(draft)
    await session.flush()
    g.draft_version_id = draft.id
    return g


async def save_draft(session: AsyncSession, g: Guide, doc: EditorDocIn) -> GuideVersion:
    doc = _clean_doc(doc)
    assert g.draft_version_id is not None
    draft = await get_version(session, g.draft_version_id)
    draft.title = doc.title
    draft.summary = doc.summary
    draft.updated_at = utcnow()
    draft.steps = _build_steps(doc)
    g.category = doc.category
    g.tags = doc.tags
    g.difficulty = doc.difficulty
    g.cover = doc.cover
    if g.status == "draft":
        g.title = doc.title
        g.summary = doc.summary
    g.updated_at = utcnow()
    await session.flush()
    return draft


def _signature(v: GuideVersion) -> tuple:
    return (
        v.title,
        v.summary,
        tuple(
            (s.key, s.title, s.body, s.minutes, tuple(i["text"] for i in s.checklist))
            for s in v.steps
        ),
    )


async def editor_doc(session: AsyncSession, g: Guide) -> EditorDoc:
    assert g.draft_version_id is not None
    draft = await get_version(session, g.draft_version_id)
    published = (
        await get_version(session, g.published_version_id) if g.published_version_id else None
    )
    fork = None
    if g.forked_from_id:
        src = await session.get(Guide, g.forked_from_id)
        if src:
            src_author = await session.get(User, src.author_id)
            fork = ForkRef(
                id=src.id,
                slug=src.slug,
                title=src.title,
                author_name=src_author.name if src_author else "",
            )
    open_suggestions = await session.scalar(
        select(func.count())
        .select_from(Suggestion)
        .where(Suggestion.guide_id == g.id, Suggestion.status == "open")
    )
    return EditorDoc(
        id=g.id,
        slug=g.slug,
        status=g.status,
        title=draft.title,
        summary=draft.summary,
        category=g.category,
        tags=g.tags,
        difficulty=g.difficulty,
        cover=g.cover,
        steps=[step_out(s) for s in draft.steps],
        published_version=version_brief(published) if published else None,
        versions=await list_versions(session, g.id),
        has_unpublished_changes=published is None or _signature(draft) != _signature(published),
        updated_at=draft.updated_at,
        forked_from=fork,
        verified=g.verified_version_id is not None,
        open_suggestions=open_suggestions or 0,
    )


def _plain(md: str) -> str:
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    return re.sub(r"[#>*_`|~-]+", " ", md)


def search_parts(
    title: str, summary: str, tags: list[str], steps: Sequence[Step]
) -> tuple[str, str, str]:
    steps_text = " ".join(
        f"{s.title}. {_plain(s.body)} {' '.join(i['text'] for i in s.checklist)}" for s in steps
    )
    return title, f"{summary} {' '.join(tags)}", re.sub(r"\s+", " ", steps_text).strip()


async def refresh_search(session: AsyncSession, g: Guide, steps: Sequence[Step]) -> None:
    a, b, c = search_parts(g.title, g.summary, g.tags, steps)
    g.search_text = f"{a}. {b}. {c}"[:20000]
    await session.flush()
    await session.execute(
        text(
            "UPDATE guides SET search_tsv = "
            "setweight(to_tsvector('russian', :a), 'A') || "
            "setweight(to_tsvector('russian', :b), 'B') || "
            "setweight(to_tsvector('russian', :c), 'C') WHERE id = :id"
        ),
        {"a": a, "b": b, "c": c[:60000], "id": g.id},
    )


def embedding_text(g: Guide, steps: Sequence[Step]) -> str:
    titles = "; ".join(s.title for s in steps)
    return f"{g.title}. {g.summary} Шаги: {titles}. Теги: {', '.join(g.tags)}"[:4000]


async def publish(session: AsyncSession, g: Guide, changelog: str) -> GuideVersion:
    assert g.draft_version_id is not None
    draft = await get_version(session, g.draft_version_id)
    if not draft.title.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Добавьте название")
    if not draft.steps:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Добавьте хотя бы один шаг")
    last = await session.scalar(
        select(func.max(GuideVersion.number)).where(GuideVersion.guide_id == g.id)
    )
    now = utcnow()
    version = GuideVersion(
        guide_id=g.id,
        number=(last or 0) + 1,
        is_draft=False,
        title=draft.title,
        summary=draft.summary,
        changelog=changelog,
        published_at=now,
    )
    version.steps = [
        Step(
            key=s.key,
            position=s.position,
            title=s.title,
            body=s.body,
            minutes=s.minutes,
            checklist=list(s.checklist),
        )
        for s in draft.steps
    ]
    session.add(version)
    await session.flush()
    g.published_version_id = version.id
    g.status = "published"
    g.title = version.title
    g.summary = version.summary
    g.steps_count = len(version.steps)
    g.est_minutes = sum(s.minutes for s in version.steps)
    g.published_at = g.published_at or now
    g.updated_at = now
    await refresh_search(session, g, version.steps)
    return version


async def fork_guide(session: AsyncSession, src: Guide, user: User) -> Guide:
    assert src.published_version_id is not None
    v = await get_version(session, src.published_version_id)
    g = Guide(
        slug=slugify(v.title),
        author_id=user.id,
        category=src.category,
        tags=list(src.tags),
        difficulty=src.difficulty,
        cover=src.cover,
        status="draft",
        title=v.title,
        summary=v.summary,
        forked_from_id=src.id,
    )
    session.add(g)
    await session.flush()
    draft = GuideVersion(guide_id=g.id, number=0, is_draft=True, title=v.title, summary=v.summary)
    # ключи шагов не трогаем, по ним форк с оригиналом сравнивается
    draft.steps = [
        Step(
            key=s.key,
            position=s.position,
            title=s.title,
            body=s.body,
            minutes=s.minutes,
            checklist=list(s.checklist),
        )
        for s in v.steps
    ]
    session.add(draft)
    await session.flush()
    g.draft_version_id = draft.id
    src.forks_count += 1
    return g
