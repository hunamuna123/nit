import copy
import hashlib
import json
import logging
import math
from datetime import timedelta
from typing import Any

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalog import CATEGORIES
from app.core.config import get_settings
from app.db import utcnow
from app.models import AiCall, User
from app.schemas import (
    AiImproveOut,
    AiReviewIssue,
    AiReviewOut,
    GuideDraft,
    GuideDraftStep,
)

log = logging.getLogger("nit.ai")

_client: httpx.AsyncClient | None = None


def client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        s = get_settings()
        _client = httpx.AsyncClient(
            base_url=s.openrouter_base_url,
            timeout=s.ai_timeout_s,
            headers={
                "Authorization": f"Bearer {s.openrouter_api_key}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Nit guides",
            },
        )
    return _client


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    # openrouter strict хочет схему без $ref и все поля required, вот и мучаемся
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(x) for x in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            return walk(copy.deepcopy(defs[node["$ref"].split("/")[-1]]))
        out: dict[str, Any] = {}
        for k, v in node.items():
            if k in ("title", "default", "description"):
                continue
            if k == "properties":
                out[k] = {name: walk(sub) for name, sub in v.items()}
            else:
                out[k] = walk(v)
        if out.get("type") == "object" and "properties" in out:
            out["required"] = list(out["properties"].keys())
            out["additionalProperties"] = False
        return out

    return walk(schema)


async def remaining_for(session: AsyncSession, user: User | None) -> int:
    s = get_settings()
    if user is None:
        return 0
    if user.role == "admin":
        return 999
    used = await session.scalar(
        select(func.count())
        .select_from(AiCall)
        .where(AiCall.user_id == user.id, AiCall.created_at > utcnow() - timedelta(hours=1))
    )
    return max(0, s.ai_user_hourly_limit - (used or 0))


async def ensure_allowed(session: AsyncSession, user: User | None) -> None:
    if not get_settings().ai_enabled:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "ИИ не настроен на сервере")
    if user is not None and await remaining_for(session, user) <= 0:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Лимит запросов к ИИ на этот час исчерпан"
        )


async def _log(
    session: AsyncSession, user: User | None, kind: str, usage: dict[str, Any], ok: bool
) -> None:
    session.add(
        AiCall(
            user_id=user.id if user else None,
            kind=kind,
            model=get_settings().ai_model,
            tokens=int(usage.get("total_tokens") or 0),
            cost_usd=float(usage.get("cost") or 0.0),
            ok=ok,
        )
    )
    await session.commit()


async def structured[T: BaseModel](
    session: AsyncSession,
    user: User | None,
    kind: str,
    system: str,
    prompt: str,
    model: type[T],
    max_tokens: int = 3000,
    temperature: float = 0.4,
) -> T:
    s = get_settings()
    body = {
        "model": s.ai_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": kind, "strict": True, "schema": strict_schema(model)},
        },
        "reasoning": {"enabled": False},
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    last_error = "пустой ответ"
    for _attempt in range(2):
        usage: dict[str, Any] = {}
        try:
            r = await client().post("/chat/completions", json=body)
            data = r.json()
            usage = data.get("usage") or {}
            if r.status_code != 200 or "choices" not in data:
                last_error = str(data.get("error", {}).get("message", r.status_code))
                await _log(session, user, kind, usage, ok=False)
                continue
            content = data["choices"][0]["message"].get("content") or ""
            parsed = model.model_validate(json.loads(_strip_fences(content)))
            await _log(session, user, kind, usage, ok=True)
            return parsed
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError, KeyError) as e:
            last_error = type(e).__name__
            await _log(session, user, kind, usage, ok=False)
    log.warning("AI %s failed: %s", kind, last_error)
    raise HTTPException(status.HTTP_502_BAD_GATEWAY, "ИИ не ответил, попробуйте ещё раз")


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0]
    return t


_CATS = ", ".join(f"{c['slug']} ({c['title']})" for c in CATEGORIES)

SYSTEM_EDITOR = f"""Ты — главный редактор платформы пошаговых инструкций «Нить».
Пользователи — студенты и новички, которые делают задачу впервые.
Правила хорошей инструкции:
- Один шаг = одно законченное действие с понятным результатом. 4–10 шагов.
- Заголовок шага — повелительное наклонение, до 70 символов («Включите виртуализацию в BIOS»).
- Текст шага — Markdown: короткие абзацы, списки, **важное жирным**, команды в блоках ```кода```,
  предупреждения через «> ». 40–160 слов на шаг.
- Чек-лист шага — 1–4 конкретных проверяемых пункта («В выводе команды видно версию 2»).
- minutes — реалистичная оценка времени шага в минутах.
- Не выдумывай точные суммы, номера статей законов, адреса и сроки — пиши «уточните в своём вузе».
- Пиши по-русски, дружелюбно и по делу, без воды и без эмодзи.
Категории (поле category — только slug): {_CATS}.
difficulty: 1 — легко, 2 — средне, 3 — сложно. tags — 2–5 коротких тегов в нижнем регистре."""


class _Hint(BaseModel):
    hint: str


class _InsightLLM(BaseModel):
    step_number: int
    diagnosis: str
    recommendation: str
    proposed_title: str
    proposed_body: str
    proposed_checklist: list[str]


class _InsightsLLM(BaseModel):
    summary: str
    items: list[_InsightLLM]


def _steps_md(steps: list[dict[str, Any]]) -> str:
    parts = []
    for i, s in enumerate(steps, 1):
        checklist = "\n".join(f"  - [ ] {c}" for c in s.get("checklist", []))
        parts.append(f"### Шаг {i}. {s['title']}\n{s.get('body', '')}\n{checklist}")
    return "\n\n".join(parts)


async def draft_from_topic(
    session: AsyncSession, user: User, topic: str, details: str
) -> GuideDraft:
    await ensure_allowed(session, user)
    if get_settings().ai_fake:
        return _fake_draft(topic)
    prompt = f"Составь пошаговую инструкцию на тему: «{topic}»."
    if details:
        prompt += f"\nУточнения от автора: {details}"
    return await structured(
        session, user, "draft", SYSTEM_EDITOR, prompt, GuideDraft, max_tokens=4000
    )


async def draft_from_text(session: AsyncSession, user: User, text: str) -> GuideDraft:
    await ensure_allowed(session, user)
    if get_settings().ai_fake:
        return _fake_draft(text[:60])
    prompt = (
        "Преврати этот текст (пост с форума, конспект, расшифровку видео) в структурированную "
        "пошаговую инструкцию. Сохрани все важные детали и команды, убери воду и повторы, "
        "добавь пропущенные очевидные шаги и чек-листы.\n\n---\n" + text[:30000]
    )
    return await structured(
        session, user, "import", SYSTEM_EDITOR, prompt, GuideDraft, max_tokens=5000
    )


_MODES = {
    "clarify": "Перепиши шаг понятнее для новичка: убери двусмысленности, добавь, где именно "
    "искать нужные кнопки/пункты, и что должно получиться в конце.",
    "simplify": "Упрости шаг: короче, проще слова, только суть. Сохрани команды.",
    "checklist": "Оставь текст почти без изменений, но составь сильный чек-лист из 2–4 "
    "проверяемых пунктов.",
    "expand": "Дополни шаг: частые ошибки, как понять, что всё получилось, что делать, "
    "если не получилось.",
    "custom": "Выполни просьбу автора.",
}


async def improve_step(
    session: AsyncSession,
    user: User,
    guide_title: str,
    step: dict[str, Any],
    mode: str,
    instruction: str,
) -> AiImproveOut:
    await ensure_allowed(session, user)
    if get_settings().ai_fake:
        return AiImproveOut(
            title=step["title"],
            body=step.get("body", "") + "\n\n> Проверьте результат, прежде чем идти дальше.",
            checklist=step.get("checklist") or ["Результат шага проверен"],
            note="Добавил проверку результата (заглушка ИИ).",
        )
    prompt = (
        f"Инструкция: «{guide_title}».\nЗадача: {_MODES.get(mode, _MODES['clarify'])}\n"
        + (f"Просьба автора: {instruction}\n" if instruction else "")
        + f"\nТекущий шаг:\n{_steps_md([step])}\n\n"
        "Верни новый заголовок, текст (Markdown), чек-лист и короткую заметку note "
        "(1 предложение: что изменил)."
    )
    return await structured(session, user, "improve", SYSTEM_EDITOR, prompt, AiImproveOut)


async def review_guide(
    session: AsyncSession, user: User, title: str, summary: str, steps: list[dict[str, Any]]
) -> AiReviewOut:
    await ensure_allowed(session, user)
    if get_settings().ai_fake:
        issues = [
            AiReviewIssue(step_index=i, severity="medium", message="Нет чек-листа для проверки.")
            for i, s in enumerate(steps)
            if not s.get("checklist")
        ]
        return AiReviewOut(
            score=max(40, 95 - 10 * len(issues)),
            verdict="Инструкция понятная, не хватает проверок результата.",
            issues=issues,
            missing_steps=[],
        )
    prompt = (
        f"Проверь инструкцию «{title}» ({summary}) как строгий редактор.\n\n{_steps_md(steps)}\n\n"
        "Найди: пропущенные шаги, неясные места, шаги, где новичок застрянет, отсутствие "
        "проверок результата, опасные действия без предупреждения. step_index — номер шага с 0, "
        "или -1 для замечаний ко всей инструкции. score — оценка качества 0–100. "
        "verdict — 1–2 предложения. missing_steps — заголовки шагов, которых не хватает."
    )
    return await structured(session, user, "review", SYSTEM_EDITOR, prompt, AiReviewOut)


async def bottleneck_insights(
    session: AsyncSession,
    user: User,
    title: str,
    steps: list[dict[str, Any]],
    problems: list[dict[str, Any]],
) -> _InsightsLLM:
    await ensure_allowed(session, user)
    if get_settings().ai_fake:
        return _InsightsLLM(
            summary="Основная потеря учеников — на сложных шагах без пошаговых подсказок.",
            items=[
                _InsightLLM(
                    step_number=p["number"],
                    diagnosis="Ученики не понимают, где искать нужный пункт.",
                    recommendation="Разбейте шаг на два и добавьте подсказки по вариантам.",
                    proposed_title=p["title"],
                    proposed_body=steps[p["number"] - 1].get("body", ""),
                    proposed_checklist=["Нужный пункт найден", "Результат проверен"],
                )
                for p in problems
            ],
        )
    blocks = []
    for p in problems:
        comments = "\n".join(f"  - «{c}»" for c in p["comments"][:12]) or "  - (нет)"
        blocks.append(
            f"Шаг {p['number']} «{p['title']}»: " + "; ".join(p["reasons"]) + f"\n"
            f"Комментарии учеников:\n{comments}"
        )
    prompt = (
        f"Инструкция «{title}». Полный текст:\n\n{_steps_md(steps)}\n\n"
        "Аналитика прохождений нашла узкие места:\n\n" + "\n\n".join(blocks) + "\n\n"
        "Для каждого узкого места: diagnosis — почему ученики спотыкаются (опирайся на "
        "комментарии и метрики, 1–2 предложения); recommendation — что конкретно поменять; "
        "proposed_title/proposed_body/proposed_checklist — готовая новая редакция шага. "
        "step_number — номер шага (с 1). summary — общий вывод в 1–2 предложениях."
    )
    return await structured(
        session, user, "insights", SYSTEM_EDITOR, prompt, _InsightsLLM, max_tokens=5000
    )


async def stuck_hint(
    session: AsyncSession,
    user: User | None,
    title: str,
    step: dict[str, Any],
    question: str,
    tips: list[str],
) -> str:
    await ensure_allowed(session, user)
    if get_settings().ai_fake:
        return "Попробуйте выполнить шаг ещё раз по пунктам чек-листа и сверить результат."
    prompt = (
        f"Ученик проходит инструкцию «{title}» и застрял на шаге:\n\n{_steps_md([step])}\n\n"
        + (f"Его вопрос: «{question}»\n" if question else "Вопроса не задал.\n")
        + (
            "Советы других учеников к этому шагу:\n" + "\n".join(f"- {t}" for t in tips[:8])
            if tips
            else ""
        )
        + "\n\nДай короткую конкретную подсказку (до 90 слов, Markdown можно), что проверить "
        "и как продвинуться. Не пересказывай шаг целиком."
    )
    out = await structured(
        session, user, "hint", SYSTEM_EDITOR, prompt, _Hint, max_tokens=600, temperature=0.3
    )
    return out.hint


async def embed(texts: list[str]) -> list[list[float]] | None:
    s = get_settings()
    if not texts:
        return []
    if s.ai_fake:
        return [_fake_vector(t) for t in texts]
    if not s.openrouter_api_key:
        return None
    try:
        r = await client().post(
            "/embeddings", json={"model": s.embedding_model, "input": texts}, timeout=15.0
        )
        data = r.json()
        rows = sorted(data["data"], key=lambda d: d["index"])
        vectors = [row["embedding"] for row in rows]
        if any(len(v) != s.embedding_dim for v in vectors):
            return None
        return vectors
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
        log.warning("embeddings failed: %s", e)
        return None


_query_cache: dict[str, list[float]] = {}


async def embed_query(q: str) -> list[float] | None:
    key = q.strip().lower()
    if key in _query_cache:
        return _query_cache[key]
    vectors = await embed([key])
    if not vectors:
        return None
    if len(_query_cache) > 500:
        _query_cache.clear()
    _query_cache[key] = vectors[0]
    return vectors[0]


def _fake_vector(text: str) -> list[float]:
    dim = get_settings().embedding_dim
    vec = [0.0] * dim
    for word in text.lower().split():
        h = int(hashlib.md5(word[:5].encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _fake_draft(topic: str) -> GuideDraft:
    topic = topic.strip().rstrip(".") or "Новая задача"
    return GuideDraft(
        title=topic[:1].upper() + topic[1:80],
        summary=f"Пошаговый план: {topic.lower()} без пропущенных шагов.",
        category="study",
        tags=["черновик", "ии"],
        difficulty=1,
        steps=[
            GuideDraftStep(
                title=title,
                body=body,
                minutes=minutes,
                checklist=checklist,
            )
            for title, body, minutes, checklist in [
                (
                    "Подготовьте всё необходимое",
                    "Соберите документы и инструменты заранее, чтобы не прерываться.",
                    5,
                    ["Всё необходимое под рукой"],
                ),
                (
                    "Выполните основное действие",
                    "Делайте по порядку и **сверяйтесь** с результатом после каждого пункта.",
                    15,
                    ["Основное действие выполнено"],
                ),
                (
                    "Проверьте результат",
                    "Убедитесь, что всё работает, и сохраните подтверждение.",
                    5,
                    ["Результат проверен", "Подтверждение сохранено"],
                ),
            ]
        ],
    )
