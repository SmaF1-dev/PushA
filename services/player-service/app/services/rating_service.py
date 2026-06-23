from sqlalchemy.orm import Session
from sqlalchemy import func
from app.domain.models import TeammateReview, ValorantProfile
from uuid import UUID

class RatingService:
    @staticmethod
    def recalculate_player_rating(db: Session, player_id: UUID):
        result = db.query(
            func.avg(TeammateReview.rating).label('average'),
            func.count(TeammateReview.id).label('count')
        ).filter(TeammateReview.target_player_id == player_id).first()

        profile = db.query(ValorantProfile).filter(ValorantProfile.player_id == player_id).first()
        
        if profile and result.count > 0:
            profile.teammate_rating = round(float(result.average), 2)
            profile.reviews_count = result.count
            db.commit()
            db.refresh(profile)
            
        return profile