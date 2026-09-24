"""Data-access for research projects and all their child artifacts."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    InsightReport,
    Persona,
    ResearchProject,
    ResearchStatus,
    SurveyQuestion,
    SurveyResponse,
)


class ResearchRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---- projects ----
    def create(self, *, owner_id: str, data: dict) -> ResearchProject:
        project = ResearchProject(owner_id=owner_id, **data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get(self, project_id: str) -> ResearchProject | None:
        return self.db.get(ResearchProject, project_id)

    def get_for_owner(self, project_id: str, owner_id: str) -> ResearchProject | None:
        return self.db.scalar(
            select(ResearchProject).where(
                ResearchProject.id == project_id, ResearchProject.owner_id == owner_id
            )
        )

    def list_for_owner(self, owner_id: str, *, limit: int, offset: int) -> list[ResearchProject]:
        return list(
            self.db.scalars(
                select(ResearchProject)
                .where(ResearchProject.owner_id == owner_id)
                .order_by(ResearchProject.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def count_for_owner(self, owner_id: str) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(ResearchProject)
                .where(ResearchProject.owner_id == owner_id)
            )
            or 0
        )

    def status_counts(self, owner_id: str) -> dict[str, int]:
        rows = self.db.execute(
            select(ResearchProject.status, func.count())
            .where(ResearchProject.owner_id == owner_id)
            .group_by(ResearchProject.status)
        ).all()
        counts = {s.value: 0 for s in ResearchStatus}
        for status_value, count in rows:
            counts[status_value] = count
        return counts

    def update(self, project: ResearchProject, **fields) -> ResearchProject:
        for key, value in fields.items():
            setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project: ResearchProject) -> None:
        self.db.delete(project)
        self.db.commit()

    # ---- child artifacts ----
    def get_personas(self, project_id: str) -> list[Persona]:
        return list(
            self.db.scalars(
                select(Persona).where(Persona.project_id == project_id).order_by(Persona.slug)
            )
        )

    def get_persona_for_owner(self, persona_id: str, owner_id: str) -> Persona | None:
        return self.db.scalar(
            select(Persona)
            .join(ResearchProject, Persona.project_id == ResearchProject.id)
            .where(Persona.id == persona_id, ResearchProject.owner_id == owner_id)
        )

    def get_questions(self, project_id: str) -> list[SurveyQuestion]:
        return list(
            self.db.scalars(
                select(SurveyQuestion)
                .where(SurveyQuestion.project_id == project_id)
                .order_by(SurveyQuestion.order_index)
            )
        )

    def get_responses(self, project_id: str) -> list[SurveyResponse]:
        return list(
            self.db.scalars(select(SurveyResponse).where(SurveyResponse.project_id == project_id))
        )

    def get_report(self, project_id: str) -> InsightReport | None:
        return self.db.scalar(
            select(InsightReport)
            .options(selectinload(InsightReport.themes))
            .where(InsightReport.project_id == project_id)
        )

    def replace_artifacts(self, project_id: str, *, personas, questions, responses, report) -> None:
        """Persist a completed run's artifacts in one transaction (idempotent per run)."""
        self.db.add_all(personas)
        self.db.add_all(questions)
        self.db.add_all(responses)
        if report is not None:
            self.db.add(report)
        self.db.commit()

    def bulk_add(self, objects: list) -> None:
        self.db.add_all(objects)
        self.db.commit()
