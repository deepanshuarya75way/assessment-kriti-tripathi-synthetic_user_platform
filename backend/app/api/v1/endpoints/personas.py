from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(tags=["personas"])


@router.post(
    "/personas/{persona_id}/chat",
    response_model=ChatResponse,
    summary="Send a message to a persona and get an in-character reply",
)
def chat_with_persona(
    persona_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    payload.validate_length()
    conversation_id, reply = ChatService(db).chat(
        persona_id=persona_id,
        owner_id=current_user.id,
        message=payload.message,
        conversation_id=payload.conversation_id,
    )
    return ChatResponse(
        conversation_id=conversation_id, reply=ChatMessageResponse.model_validate(reply)
    )

@router.get(
    "/personas/{persona_id}/conversations",
    response_model=list[ConversationResponse],
    summary="List a persona's saved chat sessiona (newest first) with their message",
)
def list_persona_conversations(
    persona_id:str,
    db:Session=Depends(get_db),
    current_user: User=Depends(get_current_user),
)-> list[ConversationResponse]:
    return ChatService(db).list_conversations(persona_id,current_user.id)
    
@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="Fetch a full persona conversation history",
)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationResponse:
    return ChatService(db).get_conversation(conversation_id, current_user.id)
