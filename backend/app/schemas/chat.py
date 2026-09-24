from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = Field(
        default=None, description="Continue an existing conversation, or omit to start a new one."
    )

    def validate_length(self) -> None:
        if len(self.message) > settings.max_chat_message_chars:
            from app.core.exceptions import ValidationAppError

            raise ValidationAppError(
                f"Message must be at most {settings.max_chat_message_chars} characters."
            )


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    order_index: int
    created_at: datetime


class ChatResponse(BaseModel):
    conversation_id: str
    reply: ChatMessageResponse


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    persona_id: str
    messages: list[ChatMessageResponse]
