from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    MessageItemResponse,
)
from app.services.chat_service import chat_service
from app.api.routes.videos import build_video_status_response

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def post_chat_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main chat interaction endpoint.
    Routes normal conversation directly or triggers background video pipeline.
    """
    try:
        response = await chat_service.handle_message(
            message_text=request.message,
            conversation_id=request.conversation_id,
            db=db,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")


@router.get("/chat/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
def get_conversation_history(conversation_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full message history and generation status for a conversation session.
    Enables rehydration and progress resumption after page reload/refresh.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    message_items = []
    active_video_id = None

    for msg in messages:
        video_meta = None
        if msg.video:
            video_meta = build_video_status_response(msg.video)
            if msg.video.status not in ("completed", "failed", "expired"):
                active_video_id = msg.video.id

        message_items.append(
            MessageItemResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                video_id=msg.video_id,
                video_metadata=video_meta,
            )
        )

    return ConversationHistoryResponse(
        conversation_id=conversation.id,
        created_at=conversation.created_at,
        messages=message_items,
        active_video_id=active_video_id,
    )
