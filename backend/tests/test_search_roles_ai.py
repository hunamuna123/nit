from fastapi.testclient import TestClient

from tests.conftest import guide_doc, make_client, publish_guide, register, run_sql


def test_search_morphology_typos_and_snippet(client: TestClient) -> None:
    register(client)
    publish_guide(client)
    publish_guide(
        client, guide_doc("Установить Docker на Windows", category="dev", tags=["docker"])
    )

    r = client.get("/api/guides", params={"q": "справки деканат"}).json()
    assert r["items"][0]["title"].startswith("Получить справку")
    assert "fts" in r["search_modes"]

    r = client.get("/api/guides", params={"q": "Dockr"}).json()
    assert r["items"] and r["items"][0]["title"].startswith("Установить Docker")
    assert "fuzzy" in r["search_modes"]

    r = client.get("/api/guides", params={"q": "номер заявки"}).json()
    assert "[[" in (r["items"][0]["snippet"] or "")

    assert (
        client.get("/api/guides", params={"q": "справку", "category": "money"}).json()["total"] == 0
    )
    docs = client.get("/api/guides", params={"q": "справку", "category": "docs"}).json()
    assert [g["category"] for g in docs["items"]] == ["docs"]


def test_expert_review_and_admin_roles(client: TestClient) -> None:
    author = register(client)
    src = publish_guide(client)

    expert = make_client()
    e = register(expert, "Эксперт")
    assert expert.get("/api/review/queue").status_code == 403

    r = expert.post(
        "/api/me/expert-request", json={"categories": ["docs"], "text": "Работаю в деканате 5 лет"}
    )
    assert r.json()["expert_request_status"] == "pending"

    admin = make_client()
    a = register(admin, "Админ")
    run_sql("UPDATE users SET role = 'admin' WHERE id = :id", {"id": a["id"]})
    pending = admin.get("/api/admin/users", params={"pending": True}).json()
    assert [u["id"] for u in pending] == [e["id"]]
    patched = admin.patch(f"/api/admin/users/{e['id']}", json={"role": "expert"}).json()
    assert patched["role"] == "expert" and patched["expert_categories"] == ["docs"]
    assert admin.get("/api/admin/stats").json()["pending_expert_requests"] == 0

    queue = expert.get("/api/review/queue").json()
    assert [q["guide"]["id"] for q in queue] == [src["id"]]
    ok = expert.post(f"/api/review/guides/{src['id']}", json={"verdict": "approved", "note": "ок"})
    assert ok.status_code == 201
    detail = client.get(f"/api/guides/{src['slug']}").json()
    assert detail["verified"] is True and detail["verified_by"]["id"] == e["id"]
    assert expert.get("/api/review/queue").json() == []
    assert client.get("/api/admin/stats").status_code == 403
    assert author["role"] == "learner"


def test_ai_tools_with_fake_model(client: TestClient) -> None:
    assert client.post("/api/ai/draft", json={"topic": "Собрать ПК"}).status_code == 401
    register(client)
    assert client.get("/api/ai/status").json()["enabled"] is True

    draft = client.post("/api/ai/draft", json={"topic": "собрать ПК"}).json()
    assert draft["title"] == "Собрать ПК" and len(draft["steps"]) == 3
    created = client.post("/api/studio/guides", json={"draft": draft}).json()
    doc = client.get(f"/api/studio/guides/{created['id']}").json()
    assert len(doc["steps"]) == 3 and doc["steps"][2]["checklist"][1]["text"]

    improved = client.post(
        "/api/ai/improve-step",
        json={"guide_title": "ПК", "step": {"title": "Шаг", "body": "Текст"}, "mode": "expand"},
    ).json()
    assert improved["body"].startswith("Текст")

    review = client.post(
        "/api/ai/review",
        json={
            "title": "ПК",
            "steps": [{"title": "A", "body": "b"}, {"title": "B", "checklist": ["x"]}],
        },
    ).json()
    assert [i["step_index"] for i in review["issues"]] == [0]
    assert run_sql("SELECT count(*) FROM ai_calls")[0][0] == 0


def test_strict_schema_inlines_refs() -> None:
    from app.schemas import GuideDraft
    from app.services.ai import strict_schema

    s = strict_schema(GuideDraft)
    step = s["properties"]["steps"]["items"]
    assert "$ref" not in str(s) and step["additionalProperties"] is False
    assert set(step["required"]) == {"title", "body", "minutes", "checklist"}
    assert "title" in s["properties"]
