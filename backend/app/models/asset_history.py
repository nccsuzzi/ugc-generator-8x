import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Index
from app.core.database import Base


class AssetHistory(Base):
    """
    Persistent log of used assets to enforce rolling exclusion / rotation (last 20 generations).
    asset_type: 'gif' or 'audio'
    """
    __tablename__ = "asset_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_type = Column(String, nullable=False, index=True)  # 'gif' | 'audio'
    asset_id = Column(String, nullable=False, index=True)
    video_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_asset_history_type_created", "asset_type", "created_at"),
    )
