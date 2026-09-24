from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ResearchStatus
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.insight import InsightReport
    from app.models.persona import Persona
    from app.models.survey import SurveyQuestion, SurveyResponse
    from app.models.user import User


class ResearchProject(UUIDMixin, TimestampMixin, Base):
    """
    A research project == one research run (the run is folded into the project;
    see docs/design-decisions.md). Holds the inputs, run status/observability and
    is the root all generated artifacts hang off.
    """

    __tablename__ = "research_projects"

    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    research_goal: Mapped[str] = mapped_column(Text, nullable=False)

    num_personas: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    num_questions: Mapped[int] = mapped_column(Integer, default=6, nullable=False)

    # ---- run status / observability (spec §7, §41) ----
    status: Mapped[str] = mapped_column(
        String(20), default=ResearchStatus.PENDING.value, index=True, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(120), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)

    owner: Mapped["User"] = relationship(back_populates="projects")
    personas: Mapped[list["Persona"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    survey_questions: Mapped[list["SurveyQuestion"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    survey_responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    insight_report: Mapped["InsightReport | None"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
