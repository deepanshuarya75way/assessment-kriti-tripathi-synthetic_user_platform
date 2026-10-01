from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.persona import Persona


class Conversation(UUIDMixin, TimestampMixin, Base):
    """A persona chat session.
    Each session belongs to exactly one researcher(''owner_id''), one project (''project_id''). 
    A persona can have several sessions; each session keeps its own persisted message history so a 
    researcher can come back later and ask follow-up questions with the earlier context.
    """

    __tablename__ = "conversations"
    
    owner_id: Mapped[str]=mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),index=True, nullable=False
    )

    persona_id: Mapped[str] = mapped_column(
        ForeignKey("personas.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("research_projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    persona: Mapped["Persona"] = relationship(back_populates="conversations")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.order_index",
    )


class ConversationMessage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversation_messages"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # user | persona
    content: Mapped[str] = mapped_column(Text, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
