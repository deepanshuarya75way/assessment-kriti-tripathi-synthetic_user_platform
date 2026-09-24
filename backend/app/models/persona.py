from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.research import ResearchProject


class Persona(UUIDMixin, TimestampMixin, Base):
    """A generated synthetic persona. ``slug`` is the pipeline-stable id (p1, p2…)."""

    __tablename__ = "personas"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. "p1"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    occupation: Mapped[str] = mapped_column(String(255), nullable=False)
    background: Mapped[str] = mapped_column(Text, nullable=False)
    personality_traits: Mapped[list] = mapped_column(JSON, default=list)
    behavioral_patterns: Mapped[list] = mapped_column(JSON, default=list)
    psychological_profile: Mapped[str] = mapped_column(Text, nullable=False)
    goals: Mapped[list] = mapped_column(JSON, default=list)
    pain_points: Mapped[list] = mapped_column(JSON, default=list)
    tech_savviness: Mapped[str] = mapped_column(String(10), nullable=False)
    communication_style: Mapped[str] = mapped_column(String(255), nullable=False)
    persona_summary: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped["ResearchProject"] = relationship(back_populates="personas")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="persona", cascade="all, delete-orphan"
    )
