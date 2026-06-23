from sqlalchemy.orm import Session
from app.domain.models import TeammateReview, ValorantProfile
from fastapi import HTTPException

class PlayerService:
    @staticmethod
    def add_review(db: Session, reviewer_id, review_data):
        if str(reviewer_id) == str(review_data.target_player_id):
            raise HTTPException(status_code=400, detail="You cannot rate yourself")

        new_review = TeammateReview(
            reviewer_id=reviewer_id,
            target_player_id=review_data.target_player_id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        db.add(new_review)
        
        profile = db.query(ValorantProfile).filter(
            ValorantProfile.player_id == review_data.target_player_id
        ).first()
        
        if profile:
            total_score = (profile.teammate_rating * profile.reviews_count) + review_data.rating
            profile.reviews_count += 1
            profile.teammate_rating = total_score / profile.reviews_count
        
        db.commit()
        return {"message": "Review added successfully"}