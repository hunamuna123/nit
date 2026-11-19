import asyncio
import os
import uuid
from collections.abc import Iterator
from typing import Any

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://nit:nit@localhost:5434/nit_test"
)
os.environ["DB_NULL_POOL"] = "true"
os.environ["AI_FAKE"] = "true"
os.environ["OPENROUTER_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa: F401
from app.db import Base
from app.main import app


def run_sql(sql: str, params: dict[str, Any] | None = None) -> list[Any]:
    async def go() -> list[Any]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.begin() as conn:
            result = await conn.execute(text(sql), params or {})
            rows = list(result.all()) if result.returns_rows else []
        await engine.dispose()
        return rows

    return asyncio.run(go())


@pytest.fixture(scope="session", autouse=True)
def schema() -> None:
    async def go() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(go())


@pytest.fixture(autouse=True)
def clean() -> None:
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    run_sql(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def make_client() -> TestClient:
    return TestClient(app)


def register(c: TestClient, name: str = "Аня", email: str | None = None) -> dict[str, Any]:
    email = email or f"{uuid.uuid4().hex[:8]}@nit.dev"
    r = c.post("/api/auth/register", json={"email": email, "name": name, "password": "secret12"})
    assert r.status_code == 201, r.text
    return r.json()


def guide_doc(title: str = "Получить справку в деканате", **over: Any) -> dict[str, Any]:
    doc = {
        "title": title,
        "summary": "Справка об обучении без очередей",
        "category": "docs",
        "tags": ["деканат", "справка"],
        "difficulty": 1,
        "cover": "torus",
        "steps": [
            {
                "title": "Узнайте, какая справка нужна",
                "body": "Уточните формат справки у того, кто её требует.",
                "minutes": 5,
                "checklist": [{"text": "Формат известен"}],
            },
            {
                "title": "Подайте заявку в личном кабинете",
                "body": "Раздел **Заявки** → «Справка об обучении».",
                "minutes": 10,
                "checklist": [{"text": "Заявка отправлена"}, {"text": "Есть номер заявки"}],
            },
            {
                "title": "Заберите справку",
                "body": "Обычно через 1–3 рабочих дня в деканате.",
                "minutes": 15,
                "checklist": [{"text": "Справка с печатью у меня"}],
            },
        ],
    }
    doc.update(over)
    return doc


def publish_guide(c: TestClient, doc: dict[str, Any] | None = None) -> dict[str, Any]:
    doc = doc or guide_doc()
    gid = c.post("/api/studio/guides", json={"title": doc["title"]}).json()["id"]
    assert c.put(f"/api/studio/guides/{gid}", json=doc).status_code == 200
    r = c.post(f"/api/studio/guides/{gid}/publish", json={"changelog": "v1"})
    assert r.status_code == 200, r.text
    return r.json()


def guest() -> tuple[TestClient, str]:
    anon = str(uuid.uuid4())
    c = TestClient(app, headers={"x-nit-anon": anon})
    return c, anon
