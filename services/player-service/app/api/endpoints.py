from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.player import PlayerCreate, PlayerResponse, ReviewCreate
from app.repositories.player_repository import PlayerRepository
from app.services.player_logic import PlayerService

router = APIRouter()

@router.post("/players", response_model=PlayerResponse)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    return PlayerRepository.create_player(db, player)

@router.post("/reviews")
def leave_review(review: ReviewCreate, db: Session = Depends(get_db)):
    dummy_reviewer_id = "00000000-0000-0000-0000-000000000000" 
    return PlayerService.add_review(db, dummy_reviewer_id, review)