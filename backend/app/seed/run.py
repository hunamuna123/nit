# фейковые прохождения по bottlenecks из content.py, чтоб аналитика на демо не была пустой

import argparse
import asyncio
import math
import random
import re
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import insert, text

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db import Base, SessionLocal, engine, utcnow
from app.models import (
    Bookmark,
    Comment,
    Guide,
    GuideVersion,
    Rating,
    Review,
    Run,
    Step,
    StepEvent,
    StepVote,
    Suggestion,
    User,
)
from app.seed.content import GUIDES, SUGGESTIONS, USERS
from app.services import ai
from app.services.guides import embedding_text, refresh_search

DEMO_PASSWORD = "demo1234"
rng = random.Random(42)

FIRST = [
    "Алексей", "Анна", "Артём", "Вера", "Глеб", "Дарина", "Денис", "Ева", "Жанна", "Захар",
    "Илья", "Карина", "Кирилл", "Лиза", "Марк", "Мила", "Никита", "Ольга", "Пётр", "Полина",
    "Роман", "Рита", "Семён", "Таня", "Ульяна", "Фёдор", "Юля", "Ян", "Ярослава", "Влад",
]  # fmt: skip
LAST = ["С.", "К.", "М.", "Л.", "В.", "Б.", "Н.", "Р.", "Т.", "Ш.", "Ж.", "Г."]

POPULARITY = {
    "sobrat-igrovoy-pk": 230,
    "spravka-ob-obuchenii": 260,
    "otchet-po-laboratornoy": 210,
    "docker-windows": 240,
    "git-pervyy-pull-request": 170,
    "python-uv-venv": 150,
    "sobrat-igrovoy-pk-razemy": 110,
}

REVIEW_NOTES = [
    "Проверил по шагам на своём опыте — всё актуально, формулировки точные.",
    "Структура хорошая, важные предупреждения на месте. Рекомендую.",
    "Актуально на текущий год, шаги проверяемые, чек-листы по делу.",
]


def key() -> str:
    return str(uuid.uuid4())


_BLOCK_START = ("- ", "* ", "> ", "#", "|", "```")


def unwrap(md: str) -> str:
    out: list[str] = []
    in_code = False
    for raw in md.strip().split("\n"):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if in_code or not out or not line.strip() or not out[-1].strip():
            out.append(line)
            continue
        prev, cur = out[-1], line.lstrip()
        numbered = re.match(r"\d+[.)]\s", cur) is not None
        if (
            prev.lstrip().startswith("```")
            or prev.lstrip().startswith("#")
            or prev.lstrip().startswith("|")
        ):
            out.append(line)
        elif cur.startswith("> ") and prev.lstrip().startswith(">"):
            out[-1] = f"{prev} {cur[2:]}"
        elif cur.startswith(_BLOCK_START) or numbered:
            out.append(line)
        else:
            out[-1] = f"{prev} {cur}"
    return "\n".join(out)


def make_steps(raw: list[dict[str, Any]], keys: list[str]) -> list[Step]:
    return [
        Step(
            key=keys[i],
            position=i,
            title=s["title"],
            body=unwrap(s["body"]),
            minutes=int(s["minutes"]),
            checklist=[{"key": key()[:8], "text": c} for c in s["checklist"]],
        )
        for i, s in enumerate(raw)
    ]


def copy_steps(steps: list[Step]) -> list[Step]:
    return [
        Step(
            key=s.key,
            position=s.position,
            title=s.title,
            body=s.body,
            minutes=s.minutes,
            checklist=[dict(i) for i in s.checklist],
        )
        for s in steps
    ]


class Gen:
    def __init__(self) -> None:
        self.runs: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.votes: dict[tuple[int, str, str], dict[str, Any]] = {}
        self.ratings: dict[tuple[int, str], dict[str, Any]] = {}

    def simulate(
        self,
        guide: Guide,
        version: GuideVersion,
        steps: list[Step],
        count: int,
        window: tuple[datetime, datetime],
        bottlenecks: dict[int, float],
        slow: dict[int, float],
        learners: list[User],
    ) -> None:
        start, end = window
        span = (end - start).total_seconds()
        for _ in range(count):
            started = start + timedelta(seconds=span * (rng.random() ** 0.7))
            registered = rng.random() < 0.45
            learner = rng.choice(learners) if registered else None
            anon = None if learner else key()
            voter = f"u:{learner.id}" if learner else f"a:{anon}"
            run_id = key()
            t = started
            done: list[str] = []
            checked: dict[str, list[str]] = {}
            current = 0
            completed = True
            stuck_total = 0
            for i, s in enumerate(steps):
                current = i
                bn = bottlenecks.get(i, 0.0)
                self._event(run_id, guide, version, s.key, "view", t, None)
                if rng.random() < 0.015 + bn * 0.85:
                    stuck_total += 1
                    self._event(
                        run_id, guide, version, s.key, "stuck", t + timedelta(minutes=1), None
                    )
                base = s.minutes * 60 * slow.get(i, 1.0) * (1 + bn * 1.5)
                seconds = max(20.0, base * math.exp(rng.gauss(0, 0.38)))
                if rng.random() < 0.025 + bn:
                    completed = False
                    t += timedelta(seconds=seconds * rng.uniform(0.3, 0.9))
                    if rng.random() < 0.08 + bn * 1.2:
                        self._vote(guide, version, s.key, voter, -1, t)
                    break
                t += timedelta(seconds=seconds)
                self._event(run_id, guide, version, s.key, "complete", t, int(seconds * 1000))
                done.append(s.key)
                checked[s.key] = [c["key"] for c in s.checklist]
                if rng.random() < 0.1 + bn * 0.6:
                    down = rng.random() < min(0.8, 0.05 + bn * 1.7)
                    self._vote(guide, version, s.key, voter, -1 if down else 1, t)
            if not completed and end - t < timedelta(minutes=20):
                t = end - timedelta(minutes=rng.randint(1, 15))
            self.runs.append(
                {
                    "id": run_id,
                    "guide_id": guide.id,
                    "version_id": version.id,
                    "user_id": learner.id if learner else None,
                    "anon_id": anon,
                    "status": "completed" if completed else "active",
                    "current_step": current,
                    "state": {"checked": checked, "done": done},
                    "started_at": started,
                    "last_activity_at": t,
                    "completed_at": t if completed else None,
                }
            )
            if completed and rng.random() < 0.42:
                pain = sum(bottlenecks.values()) + stuck_total * 0.15
                weights = [1, 2, 6, 20, 40] if pain < 0.3 else [2, 4, 12, 26, 22]
                value = rng.choices([1, 2, 3, 4, 5], weights=weights)[0]
                self.ratings[(guide.id, voter)] = {
                    "guide_id": guide.id,
                    "voter": voter,
                    "user_id": learner.id if learner else None,
                    "value": value,
                    "review": "",
                    "created_at": t + timedelta(minutes=1),
                }

    def _event(
        self,
        run_id: str,
        guide: Guide,
        version: GuideVersion,
        step_key: str,
        kind: str,
        at: datetime,
        duration: int | None,
    ) -> None:
        self.events.append(
            {
                "run_id": run_id,
                "guide_id": guide.id,
                "version_id": version.id,
                "step_key": step_key,
                "type": kind,
                "duration_ms": duration,
                "client_id": f"seed:{key()}",
                "created_at": at,
            }
        )

    def _vote(
        self,
        guide: Guide,
        version: GuideVersion,
        step_key: str,
        voter: str,
        value: int,
        at: datetime,
    ) -> None:
        self.votes[(version.id, step_key, voter)] = {
            "guide_id": guide.id,
            "version_id": version.id,
            "step_key": step_key,
            "voter": voter,
            "value": value,
            "created_at": at,
        }


async def reset() -> None:
    async with engine.begin() as conn:
        tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


async def seed() -> None:
    now = utcnow()
    pw = hash_password(DEMO_PASSWORD)
    gen = Gen()
    async with SessionLocal() as session:
        users: dict[str, User] = {}
        for k, u in USERS.items():
            users[k] = User(
                email=u["email"],
                name=u["name"],
                password_hash=pw,
                role=u["role"],
                bio=u.get("bio", ""),
                expert_categories=u.get("expert_categories", []),
                created_at=now - timedelta(days=rng.randint(70, 120)),
            )
        learners: list[User] = []
        for i in range(60):
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            learners.append(
                User(
                    email=f"learner{i + 1}@nit.demo",
                    name=name,
                    password_hash=pw,
                    created_at=now - timedelta(days=rng.randint(5, 90)),
                )
            )
        applicant = learners[0]
        applicant.expert_request_status = "pending"
        applicant.expert_request_text = (
            "Третий год работаю в студсовете и помогаю первокурсникам с документами: "
            "справки, общежитие, стипендии. Хочу проверять инструкции в этих темах."
        )
        applicant.expert_request_categories = ["docs", "home"]
        applicant.expert_requested_at = now - timedelta(hours=5)
        session.add_all([*users.values(), *learners])
        await session.flush()
        all_learners = learners + [u for k, u in users.items() if u.role == "learner"]

        by_slug: dict[str, Guide] = {}
        published: dict[str, tuple[GuideVersion, list[Step]]] = {}
        ordered = sorted(GUIDES, key=lambda g: g.get("fork_of") is not None)
        for idx, g in enumerate(ordered):
            author = users[g["author"]]
            age_days = rng.randint(22, 58) if not g.get("fork_of") else rng.randint(9, 16)
            if g.get("v1_patch"):
                age_days = 48
            created = now - timedelta(days=age_days)
            guide = Guide(
                slug=g["slug"],
                author_id=author.id,
                category=g["category"],
                tags=[t.lower() for t in g["tags"]],
                difficulty=g["difficulty"],
                cover=g["cover"],
                status="published",
                title=g["title"],
                summary=g["summary"],
                created_at=created,
                updated_at=created,
                published_at=created,
            )
            if g.get("fork_of"):
                src = by_slug[g["fork_of"]]
                guide.forked_from_id = src.id
                src.forks_count += 1
            session.add(guide)
            await session.flush()

            keys = [key() for _ in g["steps"]]
            if g.get("fork_of"):
                src_steps = published[g["fork_of"]][1]
                keys = [src_steps[i].key if i < len(src_steps) else k for i, k in enumerate(keys)]

            versions: list[
                tuple[GuideVersion, list[Step], tuple[datetime, datetime], dict, dict]
            ] = []
            patch = g.get("v1_patch")
            if patch:
                v1_keys = [keys[i] if i < len(keys) else key() for i in range(len(patch["steps"]))]
                v1_steps = make_steps(patch["steps"], v1_keys)
                v2_at = now - timedelta(days=17)
                v1 = GuideVersion(
                    guide_id=guide.id,
                    number=1,
                    is_draft=False,
                    title=g["title"],
                    summary=g["summary"],
                    changelog="Первая версия",
                    published_at=created,
                    created_at=created,
                )
                v1.steps = v1_steps
                session.add(v1)
                versions.append(
                    (
                        v1,
                        v1_steps,
                        (created, v2_at),
                        {int(k): v for k, v in patch.get("bottlenecks", {}).items()},
                        {int(k): v for k, v in patch.get("slow_steps", {}).items()},
                    )
                )
                current_at, number, changelog = v2_at, 2, patch["changelog"]
            else:
                current_at, number, changelog = created, 1, "Первая версия"

            steps = make_steps(g["steps"], keys)
            current = GuideVersion(
                guide_id=guide.id,
                number=number,
                is_draft=False,
                title=g["title"],
                summary=g["summary"],
                changelog=changelog,
                published_at=current_at,
                created_at=current_at,
            )
            current.steps = steps
            session.add(current)
            draft = GuideVersion(
                guide_id=guide.id,
                number=0,
                is_draft=True,
                title=g["title"],
                summary=g["summary"],
                created_at=current_at,
            )
            draft.steps = copy_steps(steps)
            session.add(draft)
            await session.flush()
            versions.append(
                (
                    current,
                    steps,
                    (current_at, now),
                    {int(k): v for k, v in (g.get("bottlenecks") or {}).items()},
                    {int(k): v for k, v in (g.get("slow_steps") or {}).items()},
                )
            )

            guide.published_version_id = current.id
            guide.draft_version_id = draft.id
            guide.steps_count = len(steps)
            guide.est_minutes = sum(s.minutes for s in steps)
            guide.updated_at = current_at
            if g.get("verified_by"):
                expert = users[g["verified_by"]]
                guide.verified_by_id = expert.id
                guide.verified_version_id = current.id
                guide.verified_at = current_at + timedelta(days=2)
                session.add(
                    Review(
                        guide_id=guide.id,
                        version_id=current.id,
                        expert_id=expert.id,
                        verdict="approved",
                        note=REVIEW_NOTES[idx % len(REVIEW_NOTES)],
                        created_at=guide.verified_at,
                    )
                )
            by_slug[g["slug"]] = guide
            published[g["slug"]] = (current, steps)
            await refresh_search(session, guide, steps)

            total = POPULARITY.get(g["slug"], rng.randint(55, 120))
            live = sum((w[1] - w[0]).total_seconds() for _, _, w, _, _ in versions)
            for version, vsteps, window, bns, slow in versions:
                share = (window[1] - window[0]).total_seconds() / live
                gen.simulate(
                    guide,
                    version,
                    vsteps,
                    max(8, round(total * share)),
                    window,
                    bns,
                    slow,
                    all_learners,
                )

            for step_idx, items in (g.get("comments") or {}).items():
                for user_key, body, kind in items:
                    session.add(
                        Comment(
                            guide_id=guide.id,
                            version_id=current.id,
                            step_key=steps[int(step_idx)].key,
                            user_id=users[user_key].id,
                            kind=kind,
                            body=body,
                            created_at=current_at
                            + timedelta(hours=rng.randint(6, max(7, int(age_days * 20)))),
                        )
                    )

        demo = users["demo"]
        for slug, upto in (("sobrat-igrovoy-pk", 3), ("nalogovyy-vychet-za-obuchenie", 2)):
            v, steps = published[slug]
            gen.runs.append(
                {
                    "id": key(),
                    "guide_id": by_slug[slug].id,
                    "version_id": v.id,
                    "user_id": demo.id,
                    "anon_id": None,
                    "status": "active",
                    "current_step": upto,
                    "state": {
                        "checked": {s.key: [c["key"] for c in s.checklist] for s in steps[:upto]},
                        "done": [s.key for s in steps[:upto]],
                    },
                    "started_at": now - timedelta(days=2),
                    "last_activity_at": now - timedelta(hours=3),
                    "completed_at": None,
                }
            )
        for slug in ("otchet-po-laboratornoy", "rezyume-na-stazhirovku"):
            v, steps = published[slug]
            gen.runs.append(
                {
                    "id": key(),
                    "guide_id": by_slug[slug].id,
                    "version_id": v.id,
                    "user_id": demo.id,
                    "anon_id": None,
                    "status": "completed",
                    "current_step": len(steps) - 1,
                    "state": {
                        "checked": {s.key: [c["key"] for c in s.checklist] for s in steps},
                        "done": [s.key for s in steps],
                    },
                    "started_at": now - timedelta(days=9),
                    "last_activity_at": now - timedelta(days=8),
                    "completed_at": now - timedelta(days=8),
                }
            )
        for slug in ("windows-na-novyy-ssd", "zashchita-kursovoy", "nastroit-wifi-router"):
            session.add(Bookmark(user_id=demo.id, guide_id=by_slug[slug].id))

        for i, s in enumerate(SUGGESTIONS):
            guide = by_slug[s["guide"]]
            v, steps = published[s["guide"]]
            session.add(
                Suggestion(
                    guide_id=guide.id,
                    base_version_id=v.id,
                    step_key=steps[int(s["step"])].key,
                    user_id=users[s["user"]].id,
                    title=s.get("title"),
                    body=unwrap(s["body"]),
                    message=s.get("message", "").removeprefix("Почему: "),
                    created_at=now - timedelta(hours=6 + i * 9),
                )
            )
        await session.flush()

        for chunk in range(0, len(gen.runs), 1000):
            await session.execute(insert(Run), gen.runs[chunk : chunk + 1000])
        for chunk in range(0, len(gen.events), 2000):
            await session.execute(insert(StepEvent), gen.events[chunk : chunk + 2000])
        if gen.votes:
            await session.execute(insert(StepVote), list(gen.votes.values()))
        if gen.ratings:
            await session.execute(insert(Rating), list(gen.ratings.values()))

        await session.execute(
            text(
                """
                UPDATE guides g SET
                  runs_count = (SELECT count(*) FROM runs r WHERE r.guide_id = g.id),
                  completions_count = (SELECT count(*) FROM runs r
                                       WHERE r.guide_id = g.id AND r.status = 'completed'),
                  rating_sum = COALESCE(
                    (SELECT sum(value) FROM ratings x WHERE x.guide_id = g.id), 0),
                  rating_count = (SELECT count(*) FROM ratings x WHERE x.guide_id = g.id),
                  helpful_up = (SELECT count(*) FROM step_votes v
                                WHERE v.guide_id = g.id AND v.value > 0),
                  helpful_down = (SELECT count(*) FROM step_votes v
                                  WHERE v.guide_id = g.id AND v.value < 0)
                """
            )
        )
        await session.commit()

        guides = list(by_slug.values())
        vectors = await ai.embed([embedding_text(g, published[g.slug][1]) for g in guides])
        if vectors:
            for g, vec in zip(guides, vectors, strict=True):
                g.embedding = vec
            await session.commit()
        print(
            f"Готово: {len(users) + len(learners)} пользователей, {len(guides)} инструкций, "
            f"{len(gen.runs)} прохождений, {len(gen.events)} событий, {len(gen.votes)} голосов, "
            f"{len(gen.ratings)} оценок, эмбеддинги: {'да' if vectors else 'нет'}"
        )
        print(
            f"Вход: demo@nit.demo / {DEMO_PASSWORD} (автор), admin@nit.demo, igor.vlasov@nit.demo"
        )
    await ai.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Заполнить базу демо-данными")
    parser.add_argument(
        "--reset", action="store_true", help="очистить все таблицы перед заполнением"
    )
    args = parser.parse_args()
    if args.reset:
        await reset()
    await seed()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
