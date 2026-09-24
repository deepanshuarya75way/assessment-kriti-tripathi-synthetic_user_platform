"""
Research orchestration service (spec §5, §7).

Owns the lifecycle of a research project:
  create (PENDING) → execute (RUNNING → COMPLETED/FAILED) → read artifacts.

The pipeline runs in a FastAPI background task via ``execute_research_run`` (a
module-level function that opens its own DB session, since it runs off-request).
Status is driven by real progress — never faked. On any failure the project is
marked FAILED with a safe message; the full error is logged server-side.
"""

import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import log_event, run_id_ctx
from app.db.session import session_scope
from app.models import (
    InsightReport,
    Persona,
    ResearchProject,
    ResearchStatus,
    SurveyQuestion,
    SurveyResponse,
    Theme,
)
from app.repositories.research_repository import ResearchRepository

if TYPE_CHECKING:
    from app.graph.state import GraphState

log = logging.getLogger(__name__)


class ResearchService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ResearchRepository(db)

    # ---- create / read / delete (request-scoped) ----
    def create(self, *, owner_id: str, data: dict) -> ResearchProject:
        project = self.repo.create(owner_id=owner_id, data=data)
        log_event(log, logging.INFO, "research.created", id=project.id, owner_id=owner_id)
        return project

    def _owned(self, project_id: str, owner_id: str) -> ResearchProject:
        project = self.repo.get(project_id)
        if project is None:
            raise NotFoundError("Research project not found.")
        if project.owner_id != owner_id:
            # Same message as not-found so we don't leak existence to other users.
            raise NotFoundError("Research project not found.")
        return project

    def get(self, project_id: str, owner_id: str) -> ResearchProject:
        return self._owned(project_id, owner_id)

    def list(self, owner_id: str, *, limit: int, offset: int):
        return (
            self.repo.list_for_owner(owner_id, limit=limit, offset=offset),
            self.repo.count_for_owner(owner_id),
        )

    def dashboard(self, owner_id: str):
        counts = self.repo.status_counts(owner_id)
        recent = self.repo.list_for_owner(owner_id, limit=5, offset=0)
        total = sum(counts.values())
        return counts, recent, total

    def delete(self, project_id: str, owner_id: str) -> None:
        project = self._owned(project_id, owner_id)
        self.repo.delete(project)
        log_event(log, logging.INFO, "research.deleted", id=project_id)

    def personas(self, project_id: str, owner_id: str):
        self._owned(project_id, owner_id)
        return self.repo.get_personas(project_id)

    def questions(self, project_id: str, owner_id: str):
        self._owned(project_id, owner_id)
        return self.repo.get_questions(project_id)

    def responses(self, project_id: str, owner_id: str):
        self._owned(project_id, owner_id)
        return self.repo.get_responses(project_id)

    def report(self, project_id: str, owner_id: str):
        self._owned(project_id, owner_id)
        return self.repo.get_report(project_id)


# ---------------------------------------------------------------------------
# Background execution (runs off-request, own session).
# ---------------------------------------------------------------------------


def execute_research_run(project_id: str) -> None:
    """Run the full AI pipeline for a project and persist results. Own DB session."""
    # Imported here so importing the service doesn't require langgraph in every context.
    from app.graph.graph import run_pipeline
    from app.graph.llm import active_model_label

    run_id_ctx.set(project_id)
    with session_scope() as db:
        repo = ResearchRepository(db)
        project = repo.get(project_id)
        if project is None:
            log.error("execute_research_run: project %s vanished", project_id)
            return

        repo.update(
            project,
            status=ResearchStatus.RUNNING.value,
            started_at=datetime.now(UTC),
            model_used=active_model_label(),
            error_message=None,
        )
        log_event(log, logging.INFO, "research.started", id=project_id)
        started = time.perf_counter()

        try:
            state = run_pipeline(
                product_description=project.product_description,
                target_audience=project.target_audience,
                research_goal=project.research_goal,
                num_personas=project.num_personas,
                num_questions=project.num_questions,
                run_id=project_id,
            )
            _persist_results(repo, project_id, state)
            duration = round(time.perf_counter() - started, 2)
            repo.update(
                project,
                status=ResearchStatus.COMPLETED.value,
                completed_at=datetime.now(UTC),
                duration_seconds=duration,
            )
            log_event(
                log, logging.INFO, "research.completed", id=project_id, duration_seconds=duration
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("research.failed id=%s", project_id)
            repo.update(
                project,
                status=ResearchStatus.FAILED.value,
                completed_at=datetime.now(UTC),
                duration_seconds=round(time.perf_counter() - started, 2),
                error_message="The research run failed while generating results.",
            )
            log_event(log, logging.ERROR, "research.failed", id=project_id, error=str(exc))


def _persist_results(repo: ResearchRepository, project_id: str, state: "GraphState") -> None:
    """Map the pipeline GraphState onto ORM rows."""
    personas = [
        Persona(
            project_id=project_id,
            slug=p.id,
            name=p.name,
            age=p.age,
            occupation=p.occupation,
            background=p.background,
            personality_traits=p.personality_traits,
            behavioral_patterns=p.behavioral_patterns,
            psychological_profile=p.psychological_profile,
            goals=p.goals,
            pain_points=p.pain_points,
            tech_savviness=p.tech_savviness,
            communication_style=p.communication_style,
            persona_summary=p.persona_summary,
        )
        for p in state["personas"]
    ]

    questions = [
        SurveyQuestion(
            project_id=project_id,
            slug=q.id,
            order_index=i,
            text=q.text,
            question_type=q.question_type,
            options=q.options,
            rationale=q.rationale,
        )
        for i, q in enumerate(state["survey_questions"])
    ]
    repo.bulk_add(personas + questions)  # commit so question ids exist for FKs

    slug_to_qid = {q.slug: q.id for q in questions}
    responses = []
    for r in state["survey_responses"]:
        for a in r.answers:
            qid = slug_to_qid.get(a.question_id)
            if qid is None:
                continue
            responses.append(
                SurveyResponse(
                    project_id=project_id,
                    question_id=qid,
                    persona_slug=r.persona_id,
                    answer=a.answer,
                    sentiment=a.sentiment,
                    confidence=a.confidence,
                )
            )

    ir = state["insight_report"]
    report = InsightReport(
        project_id=project_id,
        executive_summary=ir.executive_summary,
        overall_sentiment=ir.overall_sentiment,
        notable_quotes=ir.notable_quotes,
        weak_areas_or_risks=ir.weak_areas_or_risks,
        recommendations=ir.recommendations,
        themes=[
            Theme(
                title=t.title,
                description=t.description,
                prevalence=t.prevalence,
                supporting_persona_ids=t.supporting_persona_ids,
            )
            for t in ir.key_themes
        ],
    )
    repo.bulk_add(responses + [report])
