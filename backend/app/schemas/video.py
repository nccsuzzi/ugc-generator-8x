from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class VideoStatusResponse(BaseModel):
    id: str
    status: str = Field(..., description="Status: pending, extracting, planning, rendering, completed, failed, expired")
    current_stage: str = "pending"
    stage_message: str = "Preparing video generation..."
    duration: int = 7
    concept: Optional[str] = None
    text_overlay: Optional[str] = None
    background_asset_id: Optional[str] = None
    gif_asset_id: Optional[str] = None
    audio_asset_id: Optional[str] = None
    video_url: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
    licensing_tier: str = "PROTOTYPE"
    asset_sources: Optional[dict] = None
    qa_metadata: Optional[dict] = None
    is_expired: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
