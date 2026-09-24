"""Authorization tests: users can only access their own data (spec §17, §21)."""

from tests.conftest import create_completed_project


def test_endpoints_require_auth(client):
    assert client.get("/api/v1/research").status_code == 401
    assert client.get("/api/v1/research/dashboard").status_code == 401
    assert client.post("/api/v1/research", json={}).status_code == 401


def test_user_cannot_read_others_project(client, auth_headers, second_user_headers):
    project = create_completed_project(client, auth_headers)
    pid = project["id"]
    # Second user gets 404 (existence not leaked), not 403.
    assert client.get(f"/api/v1/research/{pid}", headers=second_user_headers).status_code == 404
    assert (
        client.get(f"/api/v1/research/{pid}/personas", headers=second_user_headers).status_code
        == 404
    )


def test_user_cannot_delete_others_project(client, auth_headers, second_user_headers):
    project = create_completed_project(client, auth_headers)
    assert (
        client.delete(f"/api/v1/research/{project['id']}", headers=second_user_headers).status_code
        == 404
    )
    # Still exists for the real owner.
    assert client.get(f"/api/v1/research/{project['id']}", headers=auth_headers).status_code == 200


def test_user_cannot_chat_with_others_persona(client, auth_headers, second_user_headers):
    project = create_completed_project(client, auth_headers)
    persona = client.get(f"/api/v1/research/{project['id']}/personas", headers=auth_headers).json()[
        0
    ]
    r = client.post(
        f"/api/v1/personas/{persona['id']}/chat",
        headers=second_user_headers,
        json={"message": "hi"},
    )
    assert r.status_code == 404


def test_invalid_token_rejected(client):
    assert (
        client.get("/api/v1/research", headers={"Authorization": "Bearer garbage"}).status_code
        == 401
    )
