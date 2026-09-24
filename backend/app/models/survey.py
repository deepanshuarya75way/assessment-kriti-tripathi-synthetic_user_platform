from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.research import ResearchProject


class SurveyQuestion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "survey_questions"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. "q1"
    order_index: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped["ResearchProject"] = relationship(back_populates="survey_questions")
    responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class SurveyResponse(UUIDMixin, TimestampMixin, Base):
    """
    One persona's answer to one question (the LLM's per-persona response object is
    flattened to these rows — see docs/database.md). Persona is referenced by its
    stable ``persona_slug`` within the project to keep the join simple and robust.
    """

    __tablename__ = "survey_responses"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("survey_questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    persona_slug: Mapped[str] = mapped_column(String(60), index=True, nullable=False)

    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    project: Mapped["ResearchProject"] = relationship(back_populates="survey_responses")
    question: Mapped["SurveyQuestion"] = relationship(back_populates="responses")
