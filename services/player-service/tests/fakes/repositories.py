from collections.abc import Sequence
from copy import deepcopy
from uuid import UUID

from app.domain import Player, TeammateReview, ValorantProfile
from app.repositories.interfaces import PlayerRepository, ProfileRepository, ReviewRepository


class FakePlayerRepository(PlayerRepository):
    def __init__(self, players: Sequence[Player] = ()) -> None:
        self._players = {player.id: deepcopy(player) for player in players}

    async def add(self, player: Player) -> Player:
        self._players[player.id] = deepcopy(player)
        return deepcopy(player)

    async def get_by_id(self, player_id: UUID) -> Player | None:
        player = self._players.get(player_id)
        return deepcopy(player) if player is not None else None

    async def get_by_riot_id(self, riot_id: str) -> Player | None:
        player = next(
            (player for player in self._players.values() if player.riot_id == riot_id),
            None,
        )
        return deepcopy(player) if player is not None else None

    async def exists_by_riot_id(self, riot_id: str) -> bool:
        return any(player.riot_id == riot_id for player in self._players.values())


class FakeProfileRepository(ProfileRepository):
    def __init__(self, profiles: Sequence[ValorantProfile] = ()) -> None:
        self._profiles = {profile.id: deepcopy(profile) for profile in profiles}

    async def add(self, profile: ValorantProfile) -> ValorantProfile:
        self._profiles[profile.id] = deepcopy(profile)
        return deepcopy(profile)

    async def get_by_id(self, profile_id: UUID) -> ValorantProfile | None:
        profile = self._profiles.get(profile_id)
        return deepcopy(profile) if profile is not None else None

    async def get_by_player_id(self, player_id: UUID) -> ValorantProfile | None:
        profile = next(
            (
                profile
                for profile in self._profiles.values()
                if profile.player_id == player_id
            ),
            None,
        )
        return deepcopy(profile) if profile is not None else None

    async def update(self, profile: ValorantProfile) -> ValorantProfile | None:
        if profile.id not in self._profiles:
            return None
        self._profiles[profile.id] = deepcopy(profile)
        return deepcopy(profile)


class FakeReviewRepository(ReviewRepository):
    def __init__(self, reviews: Sequence[TeammateReview] = ()) -> None:
        self._reviews = {review.id: deepcopy(review) for review in reviews}

    async def add(self, review: TeammateReview) -> TeammateReview:
        self._reviews[review.id] = deepcopy(review)
        return deepcopy(review)

    async def get_by_id(self, review_id: UUID) -> TeammateReview | None:
        review = self._reviews.get(review_id)
        return deepcopy(review) if review is not None else None

    async def list_for_target(
        self,
        target_player_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TeammateReview]:
        reviews = sorted(
            (
                review
                for review in self._reviews.values()
                if review.target_player_id == target_player_id
            ),
            key=lambda review: (review.created_at, review.id),
            reverse=True,
        )
        return deepcopy(reviews[offset : offset + limit])

    async def list_ratings_for_target(self, target_player_id: UUID) -> Sequence[int]:
        return [
            review.rating
            for review in self._reviews.values()
            if review.target_player_id == target_player_id
        ]
