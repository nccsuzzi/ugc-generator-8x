from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AssetBase(BaseModel):
    id: str
    type: str  # 'background', 'gif', 'audio'
    filename: str
    description: str
    tags: List[str] = Field(default_factory=list)
    mood: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
