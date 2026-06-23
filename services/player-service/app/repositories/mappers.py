from decimal import Decimal

from app.db.models import PlayerModel, TeammateReviewModel, ValorantProfileModel
from app.domain import Player, TeammateReview, ValorantProfile


def player_to_model(player: Player) -> PlayerModel:
    return PlayerModel(
        id=player.id,
        nickname=player.nickname,
        riot_id=player.riot_id,
        created_at=player.created_at,
        updated_at=player.updated_at,
    )


def player_to_domain(model: PlayerModel) -> Player:
    return Player(
        id=model.id,
        nickname=model.nickname,
        riot_id=model.riot_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def profile_to_model(profile: ValorantProfile) -> ValorantProfileModel:
    return ValorantProfileModel(
        id=profile.id,
        player_id=profile.player_id,
        region=profile.region,
        current_rank=profile.current_rank,
        main_roles=sorted(profile.main_roles, key=lambda role: role.value),
        status=profile.status,
        teammate_rating=Decimal(str(profile.teammate_rating)),
        reviews_count=profile.reviews_count,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def profile_to_domain(model: ValorantProfileModel) -> ValorantProfile:
    return ValorantProfile(
        id=model.id,
        player_id=model.player_id,
        region=model.region,
        current_rank=model.current_rank,
        main_roles=frozenset(model.main_roles),
        status=model.status,
        teammate_rating=float(model.teammate_rating),
        reviews_count=model.reviews_count,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def review_to_model(review: TeammateReview) -> TeammateReviewModel:
    return TeammateReviewModel(
        id=review.id,
        reviewer_id=review.reviewer_id,
        target_player_id=review.target_player_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


def review_to_domain(model: TeammateReviewModel) -> TeammateReview:
    return TeammateReview(
        id=model.id,
        reviewer_id=model.reviewer_id,
        target_player_id=model.target_player_id,
        rating=model.rating,
        comment=model.comment,
        created_at=model.created_at,
    )
