from fastapi.testclient import TestClient

from tests.conftest import guest, guide_doc, make_client, publish_guide, register


def test_draft_publish_versions(client: TestClient) -> None:
    register(client)
    gid = client.post("/api/studio/guides", json={"title": "Черновик"}).json()["id"]

    assert client.get("/api/guides").json()["total"] == 0

    doc = client.put(f"/api/studio/guides/{gid}", json=guide_doc()).json()
    assert doc["has_unpublished_changes"] is True
    keys = [s["key"] for s in doc["steps"]]

    pub = client.post(f"/api/studio/guides/{gid}/publish", json={"changelog": "v1"}).json()
    assert pub["published_version"]["number"] == 1
    assert pub["has_unpublished_changes"] is False

    slug = pub["slug"]
    detail = client.get(f"/api/guides/{slug}").json()
    assert detail["steps_count"] == 3
    assert detail["est_minutes"] == 30
    assert [s["key"] for s in detail["steps"]] == keys

    changed = guide_doc()
    changed["steps"] = [{**s, "key": k} for s, k in zip(changed["steps"], keys, strict=True)]
    changed["steps"][1]["title"] = "Подайте заявку онлайн"
    client.put(f"/api/studio/guides/{gid}", json=changed)
    v2 = client.post(f"/api/studio/guides/{gid}/publish", json={"changelog": "уточнил"}).json()
    assert v2["published_version"]["number"] == 2
    assert [v["number"] for v in v2["versions"]] == [2, 1]
    detail = client.get(f"/api/guides/{slug}").json()
    assert detail["steps"][1]["title"] == "Подайте заявку онлайн"
    assert [s["key"] for s in detail["steps"]] == keys


def test_publish_requires_steps(client: TestClient) -> None:
    register(client)
    gid = client.post("/api/studio/guides", json={"title": "Пусто"}).json()["id"]
    assert client.post(f"/api/studio/guides/{gid}/publish", json={}).status_code == 422


def test_only_author_can_edit(client: TestClient) -> None:
    register(client)
    gid = publish_guide(client)["id"]
    other = make_client()
    register(other, "Боря")
    assert other.put(f"/api/studio/guides/{gid}", json=guide_doc()).status_code == 403
    assert other.get(f"/api/studio/guides/{gid}/analytics").status_code == 403


def test_fork_keeps_step_keys(client: TestClient) -> None:
    register(client)
    src = publish_guide(client)
    other = make_client()
    register(other, "Боря")
    r = other.post(f"/api/guides/{src['slug']}/fork")
    assert r.status_code == 201
    fork_doc = other.get(f"/api/studio/guides/{r.json()['id']}").json()
    assert fork_doc["forked_from"]["slug"] == src["slug"]
    assert [s["key"] for s in fork_doc["steps"]] == [s["key"] for s in src["steps"]]
    other.post(f"/api/studio/guides/{fork_doc['id']}/publish", json={})
    forks = client.get(f"/api/guides/{src['slug']}/forks").json()
    assert len(forks) == 1 and forks[0]["forked_from"]["slug"] == src["slug"]
    assert client.get(f"/api/guides/{src['slug']}").json()["forks_count"] == 1


def test_suggestion_accept_updates_draft(client: TestClient) -> None:
    register(client)
    src = publish_guide(client)
    other = make_client()
    register(other, "Боря")
    step_key = src["steps"][1]["key"]
    r = other.post(
        f"/api/guides/{src['slug']}/suggestions",
        json={"step_key": step_key, "body": "Новый понятный текст", "message": "так яснее"},
    )
    assert r.status_code == 201

    inbox = client.get("/api/studio/suggestions").json()
    assert len(inbox) == 1 and inbox[0]["current_body"].startswith("Раздел")
    ok = client.post(f"/api/studio/suggestions/{inbox[0]['id']}/accept", json={"reply": "спасибо"})
    assert ok.json()["status"] == "accepted"
    doc = client.get(f"/api/studio/guides/{src['id']}").json()
    assert doc["steps"][1]["body"] == "Новый понятный текст"
    assert doc["has_unpublished_changes"] is True
    again = client.post(f"/api/studio/suggestions/{inbox[0]['id']}/reject", json={})
    assert again.status_code == 409


def test_comments_votes_rating_bookmark(client: TestClient) -> None:
    register(client)
    src = publish_guide(client)
    slug, key = src["slug"], src["steps"][0]["key"]

    g, _ = guest()
    assert g.post(f"/api/guides/{slug}/comments", json={"body": "?"}).status_code == 401
    assert g.post(f"/api/guides/{slug}/votes", json={"step_key": key, "value": 1}).json()["up"] == 1
    assert g.post(f"/api/guides/{slug}/votes", json={"step_key": key, "value": -1}).json() == {
        "step_key": key,
        "up": 0,
        "down": 1,
        "my_vote": -1,
    }

    c = client.post(
        f"/api/guides/{slug}/comments", json={"step_key": key, "body": "Совет", "kind": "tip"}
    )
    assert c.status_code == 201 and c.json()["is_author"] is True
    assert len(client.get(f"/api/guides/{slug}/comments", params={"step_key": key}).json()) == 1

    assert g.post(f"/api/guides/{slug}/rating", json={"value": 4}).json()["rating"] == 4.0
    assert client.post(f"/api/guides/{slug}/rating", json={"value": 5}).json()["rating"] == 4.5
    assert client.post(f"/api/guides/{slug}/bookmark").json() == {"bookmarked": True}

    detail = client.get(f"/api/guides/{slug}").json()
    assert detail["step_stats"][key] == {"up": 0, "down": 1, "comments": 1, "my_vote": None}
    assert detail["bookmarked"] is True and detail["my_rating"] == 5
    assert len(client.get("/api/me/dashboard").json()["bookmarks"]) == 1


def test_catalog_filters_and_sort(client: TestClient) -> None:
    register(client)
    publish_guide(client)
    publish_guide(client, guide_doc("Собрать игровой ПК", category="hardware", difficulty=3))
    assert client.get("/api/guides", params={"category": "hardware"}).json()["total"] == 1
    assert client.get("/api/guides", params={"difficulty": 1}).json()["total"] == 1
    for sort in ("useful", "popular", "new", "quick", "rating"):
        assert client.get("/api/guides", params={"sort": sort}).json()["total"] == 2
    cats = {c["slug"]: c["count"] for c in client.get("/api/meta/categories").json()}
    assert cats["hardware"] == 1 and cats["docs"] == 1
