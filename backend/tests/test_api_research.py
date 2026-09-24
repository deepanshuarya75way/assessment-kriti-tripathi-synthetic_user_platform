"""Research API tests — full lifecycle + artifacts (spec §21 API)."""

from tests.conftest import create_completed_project


def test_create_runs_pipeline_to_completion(client, auth_headers):
    project = create_completed_project(client, auth_headers)
    # TestClient runs the background task before returning control on the next call.
    detail = client.get(f"/api/v1/research/{project['id']}", headers=auth_headers).json()
    assert detail["status"] == "COMPLETED"
    assert detail["duration_seconds"] is not None
    assert detail["model_used"]


def test_create_validation_error(client, auth_headers):
    r = client.post(
        "/api/v1/research",
        headers=auth_headers,
        json={
            "title": "",
            "product_description": "short",
            "target_audience": "a",
            "research_goal": "g",
        },
    )
    assert r.status_code == 422


def test_persona_count_bounds_enforced(client, auth_headers):
    r = client.post(
        "/api/v1/research",
        headers=auth_headers,
        json={
            "title": "T",
            "product_description": "A valid product description here.",
            "target_audience": "Valid audience",
            "research_goal": "Valid goal",
            "num_personas": 99,
        },
    )
    assert r.status_code == 422


def test_list_pagination(client, auth_headers):
    for i in range(3):
        create_completed_project(client, auth_headers, title=f"P{i}")
    r = client.get("/api/v1/research?page=1&page_size=2", headers=auth_headers).json()
    assert r["total"] == 3 and len(r["items"]) == 2 and r["page"] == 1


def test_dashboard_counts(client, auth_headers):
    create_completed_project(client, auth_headers)
    d = client.get("/api/v1/research/dashboard", headers=auth_headers).json()
    assert d["total"] == 1 and d["completed"] == 1


def test_artifacts_endpoints(client, auth_headers):
    project = create_completed_project(client, auth_headers, num_personas=3, num_questions=4)
    pid = project["id"]
    personas = client.get(f"/api/v1/research/{pid}/personas", headers=auth_headers).json()
    survey = client.get(f"/api/v1/research/{pid}/survey", headers=auth_headers).json()
    responses = client.get(f"/api/v1/research/{pid}/responses", headers=auth_headers).json()
    insights = client.get(f"/api/v1/research/{pid}/insights", headers=auth_headers).json()
    assert len(personas) == 3
    assert len(survey) == 4
    assert len(responses) == 12
    assert insights["disclaimer"]
    assert len(insights["themes"]) >= 1


def test_report_pdf_download(client, auth_headers):
    project = create_completed_project(client, auth_headers)
    r = client.get(f"/api/v1/research/{project['id']}/report", headers=auth_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_delete_project(client, auth_headers):
    project = create_completed_project(client, auth_headers)
    assert (
        client.delete(f"/api/v1/research/{project['id']}", headers=auth_headers).status_code == 204
    )
    assert client.get(f"/api/v1/research/{project['id']}", headers=auth_headers).status_code == 404


def test_get_missing_project_404(client, auth_headers):
    assert client.get("/api/v1/research/does-not-exist", headers=auth_headers).status_code == 404
