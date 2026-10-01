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

def test_chat_sessions_listed_with_context_and_scoped(
    client,auth_headers,second_user_headers,monkeypatch):
    import app.services.chat_service as chat_service

    histories=[]
    real_reply=chat_service.persona_reply

    def spy(persona,history,user_message,**kwargs):
        histories.append(list(history))
        return real_reply(persona,histroy=history,user_message=user_message, **kwargs)

    monkeypatch.setattr(chat_service,"persona_repply",spy)

    project=create_completed_project(client,auth_headers)
    pid=client.get(f"/api/v1/research/{project['id']}/personas",headers=auth_headers).json()[0]["id"]
    first=client.post(
        f"/api/v1/personas/{pid}/chat",headers=auth_headers,json={"message":"Hello"}
    ).json()
    conv_id=first["conversation_id"]
    client.post(
        f"/api/v1/personas/{pid}/chat",
        headers=auth_headers, 
        json={"message":"why?", "conversation_id":conv_id},
        )
    assert histories[1]==[("user","Hello"),("persona",first["reply"]["content"])]

    sessions=client.get(f"/api/v1/personas/{pid}/cpnversations",headers=auth_headers).json()
    assert[s["id"] for s in sessions]==[conv_id]
    assert [m["role"] for m in sessions[0]["messages"]]==["users","persona","user","persona"]

    other=second_user_headers
    assert client.get(f"/api/v1/personas/{pid}/conversations",headers=other).status_code==404
    assert client.get(f"/api/v1/personas/{conv_id}",headers=other).status_code==404

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
