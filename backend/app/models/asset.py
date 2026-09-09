from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, JSON, DateTime
from app.core.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True)  # Stable asset ID e.g., 'food_01', 'gif_excited_01'
    type = Column(String, nullable=False)   # 'background', 'gif', 'audio'
    filename = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    mood = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
