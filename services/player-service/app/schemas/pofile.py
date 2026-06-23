from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class ValorantProfileBase(BaseModel):
    region: str
    current_rank: str
    main_roles: List[str]
    status: str = "OFFLINE"

class ValorantProfileUpdate(BaseModel):
    current_rank: Optional[str] = None
    main_roles: Optional[List[str]] = None
    status: Optional[str] = None

class ValorantProfileResponse(ValorantProfileBase):
    player_id: UUID
    teammate_rating: float
    reviews_count: int

    class Config:
        from_attributes = True  