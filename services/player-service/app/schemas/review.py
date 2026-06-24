from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class ReviewBase(BaseModel):
    target_player_id: UUID
    rating: int = Field(..., ge=1, le=5) 
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: UUID
    reviewer_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True