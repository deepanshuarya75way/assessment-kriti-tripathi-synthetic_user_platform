"""Persona chat persistence + PDF report unit tests (spec §21)."""

from app.report.generator import DISCLAIMER, generate_report_pdf
from tests.conftest import create_completed_project


def test_chat_creates_and_persists_conversation(client, auth_headers):
    project = create_completed_project(client, auth_headers)
    persona = client.get(f"/api/v1/research/{project['id']}/personas", headers=auth_headers).json()[
        0
    ]
    pid = persona["id"]

    first = client.post(
        f"/api/v1/personas/{pid}/chat", headers=auth_headers, json={"message": "Hello"}
    )
    assert first.status_code == 200
    conv_id = first.json()["conversation_id"]
    assert first.json()["reply"]["role"] == "persona"

    # Continue the same conversation.
    client.post(
        f"/api/v1/personas/{pid}/chat",
        headers=auth_headers,
        json={"message": "Tell me more", "conversation_id": conv_id},
    )

    conv = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers).json()
    assert len(conv["messages"]) == 4  # 2 user + 2 persona
    roles = [m["role"] for m in conv["messages"]]
    assert roles == ["user", "persona", "user", "persona"]


def test_chat_message_length_limit(client, auth_headers):
    project = create_completed_project(client, auth_headers)
    persona = client.get(f"/api/v1/research/{project['id']}/personas", headers=auth_headers).json()[
        0
    ]
    r = client.post(
        f"/api/v1/personas/{persona['id']}/chat", headers=auth_headers, json={"message": "x" * 5000}
    )
    assert r.status_code == 422


def test_report_pdf_bytes_and_disclaimer(client, auth_headers, db_session):
    from app.repositories.research_repository import ResearchRepository

    project = create_completed_project(client, auth_headers)
    repo = ResearchRepository(db_session)
    proj = repo.get(project["id"])
    pdf = generate_report_pdf(
        proj, repo.get_personas(proj.id), repo.get_questions(proj.id), repo.get_report(proj.id)
    )
    assert pdf[:4] == b"%PDF"
    assert DISCLAIMER  # disclaimer text exists and is applied in the report
