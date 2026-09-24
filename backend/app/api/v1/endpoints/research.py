from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ResearchProject, User
from app.report.generator import generate_report_pdf
from app.schemas.common import Page
from app.schemas.insight import InsightReportResponse
from app.schemas.persona import PersonaResponse
from app.schemas.research import (
    DashboardStats,
    ResearchCreateRequest,
    ResearchDetail,
    ResearchSummary,
)
from app.schemas.survey import SurveyQuestionResponse, SurveyResponseItem
from app.services.research_service import ResearchService, execute_research_run

router = APIRouter(prefix="/research", tags=["research"])


@router.post(
    "",
    response_model=ResearchDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a research project and start the AI pipeline",
)
def create_research(
    payload: ResearchCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResearchProject:
    service = ResearchService(db)
    project = service.create(owner_id=current_user.id, data=payload.model_dump())
    # Run the multi-minute pipeline off-request; status reflects real progress.
    background_tasks.add_task(execute_research_run, project.id)
    return project


@router.get("", response_model=Page[ResearchSummary], summary="List the current user's projects")
def list_research(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Page[ResearchSummary]:
    service = ResearchService(db)
    items, total = service.list(current_user.id, limit=page_size, offset=(page - 1) * page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/dashboard", response_model=DashboardStats, summary="Dashboard counts + recent projects"
)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStats:
    counts, recent, total = ResearchService(db).dashboard(current_user.id)
    return DashboardStats(
        total=total,
        completed=counts["COMPLETED"],
        running=counts["RUNNING"],
        failed=counts["FAILED"],
        pending=counts["PENDING"],
        recent=recent,
    )


@router.get(
    "/{project_id}", response_model=ResearchDetail, summary="Get one project (with run status)"
)
def get_research(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResearchProject:
    return ResearchService(db).get(project_id, current_user.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a project")
def delete_research(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ResearchService(db).delete(project_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/personas",
    response_model=list[PersonaResponse],
    summary="Generated personas for a project",
)
def get_personas(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ResearchService(db).personas(project_id, current_user.id)


@router.get(
    "/{project_id}/survey",
    response_model=list[SurveyQuestionResponse],
    summary="Survey questions for a project",
)
def get_survey(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ResearchService(db).questions(project_id, current_user.id)


@router.get(
    "/{project_id}/responses",
    response_model=list[SurveyResponseItem],
    summary="Per-persona survey responses",
)
def get_responses(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ResearchService(db).responses(project_id, current_user.id)


@router.get(
    "/{project_id}/insights",
    response_model=InsightReportResponse | None,
    summary="Insight report for a project (null until completed)",
)
def get_insights(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ResearchService(db).report(project_id, current_user.id)


@router.get(
    "/{project_id}/report",
    summary="Download the research report as a PDF",
    responses={200: {"content": {"application/pdf": {}}}},
)
def get_report_pdf(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    service = ResearchService(db)
    project = service.get(project_id, current_user.id)
    personas = service.personas(project_id, current_user.id)
    questions = service.questions(project_id, current_user.id)
    report = service.report(project_id, current_user.id)
    pdf_bytes = generate_report_pdf(project, personas, questions, report)
    filename = f"research_report_{project_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
