import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, JSON, DateTime
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    target_audience = Column(Text, nullable=True)
    benefits = Column(JSON, default=list, nullable=False)
    marketing_angles = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
