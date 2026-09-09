import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.video import Video
from app.schemas.chat import ChatResponse
from app.services.groq_service import groq_service
from app.services.video_service import video_service
from app.utils.url_utils import is_video_generation_intent

logger = logging.getLogger(__name__)


class ChatService:
    """
    Handles conversational interactions, intent routing, and background video triggering.
    """

    async def handle_message(self, message_text: str, conversation_id: Optional[str], db: Session) -> ChatResponse:
        # 1. Resolve or create Conversation
        conversation = None
        if conversation_id:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        
        if not conversation:
            conversation = Conversation()
            db.add(conversation)
            db.flush()

        # 2. Persist User Message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=message_text,
        )
        db.add(user_msg)
        db.flush()

        # 3. Deterministic Intent Detection
        should_generate_video, detected_url = is_video_generation_intent(message_text)

        if should_generate_video and detected_url:
            # Video Generation Path
            video = Video(status="pending")
            db.add(video)
            db.flush()

            # Product name extraction heuristic from prompt or domain
            name_hint = "your product"
            if "building" in message_text.lower():
                # e.g., "I'm building CalAI"
                part = message_text.split("building", 1)[1].split(",")[0].split(".")[0].strip()
                if part:
                    name_hint = part

            assistant_reply = f"Got it — I'll create a short UGC-style video for {name_hint}."
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_reply,
                video_id=video.id,
            )
            db.add(assistant_msg)
            db.commit()

            # In Vercel serverless / AWS Lambda, unawaited background tasks freeze upon response completion.
            # Await the pipeline so the render completes within this single function invocation.
            import os
            is_serverless = bool(
                os.environ.get("VERCEL")
                or os.environ.get("VERCEL_ENV")
                or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
                or os.environ.get("SERVERLESS")
            )
            if is_serverless:
                logger.info(f"Serverless environment detected (VERCEL={os.environ.get('VERCEL')}). Running video pipeline synchronously in this invocation...")
                await video_service.generate_video_pipeline(
                    video_id=video.id,
                    url=detected_url,
                    user_hint=message_text,
                )
            else:
                asyncio.create_task(
                    video_service.generate_video_pipeline(
                        video_id=video.id,
                        url=detected_url,
                        user_hint=message_text,
                    )
                )

            return ChatResponse(
                message=assistant_reply,
                video_id=video.id,
                generation_started=True,
                conversation_id=conversation.id,
            )

        # Conversational Path (e.g. "hi", "what can you do?")
        assistant_reply = groq_service.generate_conversational_response(message_text)
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_reply,
            video_id=None,
        )
        db.add(assistant_msg)
        db.commit()

        return ChatResponse(
            message=assistant_reply,
            video_id=None,
            generation_started=False,
            conversation_id=conversation.id,
        )


chat_service = ChatService()
