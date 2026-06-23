from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class PlayerBase(BaseModel):
    nickname: str
    riot_id: str

class PlayerCreate(PlayerBase):
    region: str
    current_rank: str
    main_roles: List[str]

class ReviewCreate(BaseModel):
    target_player_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class PlayerResponse(PlayerBase):
    id: UUID
    class Config:
        from_attributes = True