from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.video import VideoStatusResponse


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, description="Optional existing conversation ID")
    message: str = Field(..., min_length=1, description="Message text from the user")


class ChatResponse(BaseModel):
    message: str
    video_id: Optional[str] = None
    generation_started: bool = False
    conversation_id: str


class MessageItemResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime
    video_id: Optional[str] = None
    video_metadata: Optional[VideoStatusResponse] = None


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    created_at: datetime
    messages: List[MessageItemResponse]
    active_video_id: Optional[str] = None
