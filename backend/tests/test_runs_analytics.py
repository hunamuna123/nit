import uuid
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import guest, publish_guide, register, run_sql


def _ev(kind: str, key: str, ms: int | None = None) -> dict[str, Any]:
    return {"client_id": uuid.uuid4().hex, "type": kind, "step_key": key, "duration_ms": ms}


def _walk(slug: str, steps: list[dict[str, Any]], upto: int, finish: bool) -> str:
    g, _ = guest()
    run = g.post(f"/api/guides/{slug}/runs").json()
    events, done = [], []
    for i in range(upto + 1):
        events.append(_ev("view", steps[i]["key"]))
        if i < upto or finish:
            events.append(_ev("complete", steps[i]["key"], 60_000 * (i + 1)))
            done.append(steps[i]["key"])
    body = {
        "current_step": upto,
        "state": {"checked": {}, "done": done},
        "events": events,
        "completed": finish,
    }
    assert g.post(f"/api/runs/{run['id']}/sync", json=body).status_code == 200
    return run["id"]


def test_run_sync_is_idempotent_and_completes(client: TestClient) -> None:
    register(client)
    src = publish_guide(client)
    steps = src["steps"]
    g, _ = guest()
    run = g.post(f"/api/guides/{src['slug']}/runs").json()
    assert g.post(f"/api/guides/{src['slug']}/runs").json()["id"] == run["id"]

    events = [_ev("view", steps[0]["key"]), _ev("complete", steps[0]["key"], 1000)]
    body = {
        "current_step": 1,
        "state": {"checked": {steps[0]["key"]: [steps[0]["checklist"][0]["key"], "bogus"]}},
        "events": events,
    }
    first = g.post(f"/api/runs/{run['id']}/sync", json=body).json()
    assert first["state"]["checked"][steps[0]["key"]] == [steps[0]["checklist"][0]["key"]]
    g.post(f"/api/runs/{run['id']}/sync", json=body)
    assert run_sql("SELECT count(*) FROM step_events")[0][0] == 2

    other, _ = guest()
    assert other.get(f"/api/runs/{run['id']}").status_code == 403

    done = {"current_step": 2, "state": {"done": [s["key"] for s in steps]}, "completed": True}
    assert g.post(f"/api/runs/{run['id']}/sync", json=done).json()["status"] == "completed"
    detail = client.get(f"/api/guides/{src['slug']}").json()
    assert detail["runs_count"] == 1 and detail["completions_count"] == 1


def test_stuck_help_returns_tips_and_counts(client: TestClient) -> None:
    register(client)
    src = publish_guide(client)
    key = src["steps"][1]["key"]
    client.post(
        f"/api/guides/{src['slug']}/comments",
        json={"step_key": key, "body": "Ищите раздел Заявки внизу", "kind": "tip"},
    )
    g, _ = guest()
    run = g.post(f"/api/guides/{src['slug']}/runs").json()
    r = g.post(f"/api/runs/{run['id']}/help", json={"step_key": key, "question": "где?"}).json()
    assert r["ai"] is True and r["hint"]
    assert r["tips"][0]["body"] == "Ищите раздел Заявки внизу"
    assert run_sql("SELECT count(*) FROM step_events WHERE type = 'stuck'")[0][0] == 1


def test_analytics_finds_bottleneck(client: TestClient) -> None:
    register(client)
    src = publish_guide(client)
    slug, steps = src["slug"], src["steps"]
    for _ in range(4):
        _walk(slug, steps, 2, finish=True)
    for _ in range(6):
        _walk(slug, steps, 1, finish=False)
    _walk(slug, steps, 0, finish=False)
    run_sql("UPDATE runs SET last_activity_at = now() - interval '2 hours' WHERE status = 'active'")

    a = client.get(f"/api/studio/guides/{src['id']}/analytics").json()
    t = a["totals"]
    assert (t["runs"], t["completed"], t["abandoned"]) == (11, 4, 7)
    s1 = a["steps"][1]
    assert (s1["reached"], s1["dropped"]) == (10, 6)
    assert s1["level"] == "critical" and s1["reasons"][0].startswith("Бросают 60%")
    assert a["bottlenecks"][0] == steps[1]["key"]
    assert a["steps"][2]["level"] == "ok"

    insights = client.post(f"/api/studio/guides/{src['id']}/insights").json()
    assert insights["items"][0]["step_key"] == steps[1]["key"]

    studio = client.get("/api/studio/guides").json()
    assert studio[0]["hot_step"]["key"] == steps[1]["key"]
