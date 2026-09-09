from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    url: str
    name: str
    description: str
    category: str
    target_audience: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    marketing_angles: List[str] = Field(default_factory=list)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
