import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, LargeBinary, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="pending", nullable=False, index=True)
    # statuses: pending, extracting, planning, rendering, completed, failed
    current_stage = Column(String, default="pending", nullable=False)
    # stages: extracting, analyzing, searching_assets, adapting_audio, rendering, validating, completed, failed
    stage_message = Column(String, default="Preparing video generation...", nullable=False)

    concept = Column(String, nullable=True)
    duration = Column(Integer, default=7, nullable=False)
    
    background_asset_id = Column(String, nullable=True)
    gif_asset_id = Column(String, nullable=True)
    audio_asset_id = Column(String, nullable=True)
    
    text_overlay = Column(String, nullable=True)
    text_style = Column(String, default="bold_stroke_shadow", nullable=False)
    gif_position = Column(String, default="top", nullable=False)
    gif_scale = Column(Float, default=0.70, nullable=False)
    
    # Store video bytes directly in PostgreSQL BYTEA
    video_data = Column(LargeBinary, nullable=True)
    content_type = Column(String, default="video/mp4", nullable=False)
    
    # Licensing Gate & Provenance Metadata
    licensing_tier = Column(String, default="PROTOTYPE", nullable=False)
    asset_sources = Column(JSON, nullable=True)
    qa_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

    product = relationship("Product")
