from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.domain import TeammateReview


class ReviewRepository(ABC):
    """Define persistence operations required for teammate reviews."""

    @abstractmethod
    async def add(self, review: TeammateReview) -> TeammateReview:
        """Persist a teammate review.

        :param review: Domain review to persist.
        :returns: Persisted review.
        """

    @abstractmethod
    async def get_by_id(self, review_id: UUID) -> TeammateReview | None:
        """Find a review by ID.

        :param review_id: Review UUID.
        :returns: Review or ``None`` when absent.
        """

    @abstractmethod
    async def list_for_target(
        self,
        target_player_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TeammateReview]:
        """Return reviews received by a player, newest first.

        :param target_player_id: UUID of the reviewed player.
        :param limit: Maximum number of reviews to return.
        :param offset: Number of reviews to skip.
        :returns: Ordered sequence of reviews.
        """

    @abstractmethod
    async def list_ratings_for_target(self, target_player_id: UUID) -> Sequence[int]:
        """Return ratings used to recalculate an aggregate rating.

        :param target_player_id: UUID of the reviewed player.
        :returns: Sequence of integer ratings.
        """
