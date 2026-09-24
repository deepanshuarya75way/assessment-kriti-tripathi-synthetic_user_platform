from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.research import ResearchProject


class InsightReport(UUIDMixin, TimestampMixin, Base):
    """One insight report per project (1:1). Simple string lists are stored as JSON;
    themes are normalized into their own table because they carry structure."""

    __tablename__ = "insight_reports"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    overall_sentiment: Mapped[str] = mapped_column(String(10), nullable=False)
    notable_quotes: Mapped[list] = mapped_column(JSON, default=list)
    weak_areas_or_risks: Mapped[list] = mapped_column(JSON, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)

    project: Mapped["ResearchProject"] = relationship(back_populates="insight_report")
    themes: Mapped[list["Theme"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class Theme(UUIDMixin, Base):
    __tablename__ = "themes"

    report_id: Mapped[str] = mapped_column(
        ForeignKey("insight_reports.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prevalence: Mapped[str] = mapped_column(String(10), nullable=False)
    supporting_persona_ids: Mapped[list] = mapped_column(JSON, default=list)

    report: Mapped["InsightReport"] = relationship(back_populates="themes")
