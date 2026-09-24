"""Auth API tests — success and failure cases (spec §21 API)."""


def test_register_returns_token(client):
    r = client.post(
        "/api/v1/auth/register", json={"email": "new@example.com", "password": "password123"}
    )
    assert r.status_code == 201
    assert r.json()["access_token"]


def test_register_duplicate_email_conflicts(client):
    body = {"email": "dup@example.com", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=body).status_code == 201
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


def test_register_short_password_rejected(client):
    r = client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "short"})
    assert r.status_code == 422
    assert r.json()["success"] is False


def test_login_success_and_failure(client):
    client.post(
        "/api/v1/auth/register", json={"email": "log@example.com", "password": "password123"}
    )
    ok = client.post(
        "/api/v1/auth/login", json={"email": "log@example.com", "password": "password123"}
    )
    assert ok.status_code == 200
    bad = client.post(
        "/api/v1/auth/login", json={"email": "log@example.com", "password": "wrongpass"}
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_current_user(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200 and r.json()["email"] == "user@example.com"
