from collections.abc import Sequence
from uuid import UUID

from app.domain import TeammateReview
from app.repositories.interfaces import PlayerRepository, ProfileRepository, ReviewRepository

from .exceptions import PlayerNotFoundError, ProfileNotFoundError
from .transactions import TransactionManager


class ReviewService:
    """Coordinate review and aggregate-rating use cases.

    :param players: Player repository implementation.
    :param profiles: Valorant profile repository implementation.
    :param reviews: Teammate review repository implementation.
    :param transaction: Transaction boundary used by write operations.
    """

    def __init__(
        self,
        players: PlayerRepository,
        profiles: ProfileRepository,
        reviews: ReviewRepository,
        transaction: TransactionManager,
    ) -> None:
        self._players = players
        self._profiles = profiles
        self._reviews = reviews
        self._transaction = transaction

    async def create_review(
        self,
        *,
        reviewer_id: UUID,
        target_player_id: UUID,
        rating: int,
        comment: str | None = None,
    ) -> TeammateReview:
        """Create a review and recalculate the target player's rating atomically.

        :param reviewer_id: UUID of the reviewing player.
        :param target_player_id: UUID of the reviewed player.
        :param rating: Integer rating from one to five.
        :param comment: Optional review text.
        :returns: Persisted teammate review.
        :raises InvalidReviewError: If the review violates domain rules.
        :raises PlayerNotFoundError: If either player does not exist.
        :raises ProfileNotFoundError: If the target player has no profile.
        """
        try:
            review = TeammateReview(
                reviewer_id=reviewer_id,
                target_player_id=target_player_id,
                rating=rating,
                comment=comment,
            )

            if await self._players.get_by_id(reviewer_id) is None:
                raise PlayerNotFoundError(reviewer_id)
            if await self._players.get_by_id(target_player_id) is None:
                raise PlayerNotFoundError(target_player_id)

            profile = await self._profiles.get_by_player_id_for_update(
                target_player_id
            )
            if profile is None:
                raise ProfileNotFoundError(target_player_id)

            persisted_review = await self._reviews.add(review)
            ratings = await self._reviews.list_ratings_for_target(target_player_id)
            profile.recalculate_rating(ratings)
            if await self._profiles.update(profile) is None:
                raise ProfileNotFoundError(target_player_id)

            await self._transaction.commit()
            return persisted_review
        except Exception:
            await self._transaction.rollback()
            raise

    async def list_reviews(
        self,
        target_player_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TeammateReview]:
        """List reviews received by a player.

        :param target_player_id: UUID of the reviewed player.
        :param limit: Maximum number of reviews to return.
        :param offset: Number of reviews to skip.
        :returns: Reviews ordered from newest to oldest.
        :raises PlayerNotFoundError: If the target player does not exist.
        """
        if await self._players.get_by_id(target_player_id) is None:
            raise PlayerNotFoundError(target_player_id)
        return await self._reviews.list_for_target(
            target_player_id, limit=limit, offset=offset
        )
