"""
Seed the database with a demo user and one completed research project.

Runs the real pipeline (in whatever LLM mode is configured — 'fake' by default),
so the seeded project has genuine generated artifacts, not hand-written fixtures.

Usage:
    python -m scripts.seed
Demo login:  demo@example.com / demopassword123
"""

import logging

from app.core.security import hash_password
from app.db.base import Base, engine
from app.db.session import session_scope
from app.models import User
from app.repositories.research_repository import ResearchRepository
from app.services.research_service import execute_research_run

logging.getLogger().setLevel(logging.WARNING)

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demopassword123"


def main() -> None:
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    with session_scope() as db:
        user = db.query(User).filter(User.email == DEMO_EMAIL).one_or_none()
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                full_name="Demo User",
                hashed_password=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            db.flush()
        repo = ResearchRepository(db)
        project = repo.create(
            owner_id=user.id,
            data={
                "title": "Placement Prep AI — MVP feature research",
                "product_description": (
                    "Placement Prep AI: a campus-to-corporate readiness platform that helps "
                    "final-year students prepare for company-specific placement interviews with "
                    "synthetic interviewer personas, resume feedback and weak-area analytics."
                ),
                "target_audience": (
                    "Final-year engineering students at tier-2/tier-3 colleges with limited access "
                    "to real mock interviews, plus Training & Placement cell officers."
                ),
                "research_goal": "Decide which features to prioritize for the MVP launch.",
                "num_personas": 4,
                "num_questions": 6,
            },
        )
        project_id = project.id

    # Runs with its own session and marks the project COMPLETED.
    execute_research_run(project_id)
    print(f"Seeded demo user {DEMO_EMAIL} (password: {DEMO_PASSWORD}) and project {project_id}.")


if __name__ == "__main__":
    main()
