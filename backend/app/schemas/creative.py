from typing import Optional
from pydantic import BaseModel, Field


class CreativePlan(BaseModel):
    concept: str = Field(..., description="Creative concept hook, e.g., 'POV: finally making calorie tracking easy'")
    duration: int = Field(default=7, ge=5, le=10, description="Video duration in seconds")
    background_asset_id: str = Field(..., description="Stable asset ID of background video")
    gif_asset_id: str = Field(..., description="Stable asset ID of reaction GIF")
    audio_asset_id: str = Field(..., description="Stable asset ID of audio track")
    text_overlay: str = Field(..., description="Short trendy hook text for video")
    text_style: str = Field(default="bold_center", description="Style of text overlay")
    gif_position: str = Field(default="center", description="Position of reaction GIF (center, top, bottom)")
    gif_scale: float = Field(default=0.55, ge=0.2, le=1.0, description="Scale of reaction GIF")
