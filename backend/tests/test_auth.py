from fastapi.testclient import TestClient

from tests.conftest import guest, publish_guide, register, run_sql


def test_register_login_logout(client: TestClient) -> None:
    me = register(client, "Аня", "anya@nit.dev")
    assert me["role"] == "learner"
    assert client.get("/api/auth/me").json()["user"]["email"] == "anya@nit.dev"

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").json()["user"] is None

    bad = client.post("/api/auth/login", json={"email": "anya@nit.dev", "password": "nope"})
    assert bad.status_code == 401
    ok = client.post("/api/auth/login", json={"email": "ANYA@nit.dev", "password": "secret12"})
    assert ok.status_code == 200
    assert client.get("/api/auth/me").json()["user"]["name"] == "Аня"


def test_duplicate_email(client: TestClient) -> None:
    register(client, email="dup@nit.dev")
    r = client.post(
        "/api/auth/register", json={"email": "dup@nit.dev", "name": "Ещё", "password": "secret12"}
    )
    assert r.status_code == 409


def test_guest_progress_moves_to_account(client: TestClient) -> None:
    register(client)
    slug = publish_guide(client)["slug"]

    g, anon = guest()
    run = g.post(f"/api/guides/{slug}/runs").json()
    g.post(f"/api/guides/{slug}/rating", json={"value": 5})

    r = g.post(
        "/api/auth/register",
        json={"email": "new@nit.dev", "name": "Гость", "password": "secret12", "anon_id": anon},
    )
    assert r.status_code == 201
    user_id = r.json()["id"]
    assert run_sql("SELECT user_id FROM runs WHERE id = :id", {"id": run["id"]})[0][0] == user_id
    assert run_sql("SELECT voter FROM ratings")[0][0] == f"u:{user_id}"
