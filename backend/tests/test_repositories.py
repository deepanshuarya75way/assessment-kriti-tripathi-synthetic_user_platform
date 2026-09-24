"""Database CRUD, relationship and cascade tests (spec §21 database)."""

from app.core.security import hash_password
from app.models import Persona, ResearchStatus
from app.repositories.research_repository import ResearchRepository
from app.repositories.user_repository import UserRepository


def _make_user(db):
    return UserRepository(db).create(
        email="repo@example.com", hashed_password=hash_password("password123"), full_name="Repo"
    )


def test_user_create_and_get_by_email(db_session):
    user = _make_user(db_session)
    fetched = UserRepository(db_session).get_by_email("repo@example.com")
    assert fetched is not None and fetched.id == user.id


def test_research_crud(db_session):
    user = _make_user(db_session)
    repo = ResearchRepository(db_session)
    project = repo.create(
        owner_id=user.id,
        data={
            "title": "T",
            "product_description": "p",
            "target_audience": "a",
            "research_goal": "g",
            "num_personas": 3,
            "num_questions": 4,
        },
    )
    assert project.status == ResearchStatus.PENDING.value

    repo.update(project, status=ResearchStatus.COMPLETED.value)
    assert repo.get(project.id).status == ResearchStatus.COMPLETED.value

    items = repo.list_for_owner(user.id, limit=10, offset=0)
    assert len(items) == 1
    assert repo.count_for_owner(user.id) == 1

    repo.delete(project)
    assert repo.get(project.id) is None


def test_status_counts(db_session):
    user = _make_user(db_session)
    repo = ResearchRepository(db_session)
    for status in [ResearchStatus.COMPLETED, ResearchStatus.COMPLETED, ResearchStatus.FAILED]:
        p = repo.create(
            owner_id=user.id,
            data={
                "title": "T",
                "product_description": "p",
                "target_audience": "a",
                "research_goal": "g",
            },
        )
        repo.update(p, status=status.value)
    counts = repo.status_counts(user.id)
    assert counts["COMPLETED"] == 2 and counts["FAILED"] == 1


def test_cascade_delete_removes_children(db_session):
    user = _make_user(db_session)
    repo = ResearchRepository(db_session)
    project = repo.create(
        owner_id=user.id,
        data={
            "title": "T",
            "product_description": "p",
            "target_audience": "a",
            "research_goal": "g",
        },
    )
    db_session.add(
        Persona(
            project_id=project.id,
            slug="p1",
            name="N",
            age=30,
            occupation="o",
            background="b",
            personality_traits=[],
            behavioral_patterns=[],
            psychological_profile="pp",
            goals=[],
            pain_points=[],
            tech_savviness="low",
            communication_style="c",
            persona_summary="s",
        )
    )
    db_session.commit()
    assert len(repo.get_personas(project.id)) == 1
    repo.delete(project)
    assert repo.get_personas(project.id) == []
