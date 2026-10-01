"""
Persona chat service (spec §15 Persona Chat).

Conversation history is persisted, so a chat survives restarts and can be
reopened later. History is loaded from the DB and passed to the stateless
persona-reply helper — the agent module holds no per-session state.
"""

import logging

from sqlalchemy.orm import Session

from app.agents.interview_agent import persona_reply
from app.core.exceptions import NotFoundError
from app.core.logging import log_event
from app.models import MessageRole, Persona
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.research_repository import ResearchRepository

log = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.research = ResearchRepository(db)
        self.conversations = ConversationRepository(db)

    def _persona_dict(self, persona: Persona) -> dict:
        return {
            "id": persona.id,
            "slug": persona.slug,
            "name": persona.name,
            "age": persona.age,
            "occupation": persona.occupation,
            "background": persona.background,
            "personality_traits": persona.personality_traits,
            "behavioral_patterns": persona.behavioral_patterns,
            "psychological_profile": persona.psychological_profile,
            "goals": persona.goals,
            "pain_points": persona.pain_points,
            "tech_savviness": persona.tech_savviness,
            "communication_style": persona.communication_style,
        }

    def chat(self, *, persona_id: str, owner_id: str, message: str, conversation_id: str | None):
        persona = self.research.get_persona_for_owner(persona_id, owner_id)
        if persona is None:
            raise NotFoundError("Persona not found.")

        if conversation_id:
            conversation = self.conversations.get(conversation_id)
            if conversation is None or conversation.persona_id != persona_id:
                raise NotFoundError("Conversation not found.")
        else:
            conversation = self.conversations.create(
                persona_id=persona_id, project_id=persona.project_id
            )

        history = [
            (m.role, m.content) for m in sorted(conversation.messages, key=lambda m: m.order_index)
        ]

        project = self.research.get(persona.project_id)
        reply_text = persona_reply(
            self._persona_dict(persona),
            history=history,
            user_message=message,
            product_description=project.product_description if project else "",
        )

        idx = self.conversations.next_index(conversation.id)
        self.conversations.add_message(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            content=message,
            order_index=idx,
        )
        reply = self.conversations.add_message(
            conversation_id=conversation.id,
            role=MessageRole.PERSONA.value,
            content=reply_text,
            order_index=idx + 1,
        )
        log_event(
            log,
            logging.INFO,
            "persona.chat",
            persona_id=persona_id,
            conversation_id=conversation.id,
        )
        return conversation.id, reply

    def list_conversations(self,persona_id:str,owner_id:str):
        persona=self.research.get_persona_for_owner(persona_id,owner_id)
        if persona is None:
            raise NotFoundError("persona not found.")
        return self.conversations.list_for_persona(persona_id)

    def get_conversation(self, conversation_id: str, owner_id: str):
        conversation = self.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found.")
        persona = self.research.get_persona_for_owner(conversation.persona_id, owner_id)
        if persona is None:
            raise NotFoundError("Conversation not found.")
        return conversation
