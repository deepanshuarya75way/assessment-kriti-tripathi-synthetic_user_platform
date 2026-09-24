"""Data-access for persona chat conversations and messages."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Conversation, ConversationMessage


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, persona_id: str, project_id: str) -> Conversation:
        conv = Conversation(persona_id=persona_id, project_id=project_id)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def get(self, conversation_id: str) -> Conversation | None:
        return self.db.scalar(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )

    def next_index(self, conversation_id: str) -> int:
        current = self.db.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
        )
        return current or 0

    def add_message(
        self, *, conversation_id: str, role: str, content: str, order_index: int
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id, role=role, content=content, order_index=order_index
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg
