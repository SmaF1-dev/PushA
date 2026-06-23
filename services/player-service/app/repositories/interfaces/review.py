from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.domain import TeammateReview


class ReviewRepository(ABC):
    @abstractmethod
    async def add(self, review: TeammateReview) -> TeammateReview:
        """Persist and return a teammate review."""

    @abstractmethod
    async def get_by_id(self, review_id: UUID) -> TeammateReview | None:
        """Return a review by ID, if it exists."""

    @abstractmethod
    async def list_for_target(
        self,
        target_player_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TeammateReview]:
        """Return reviews received by a player, newest first."""

    @abstractmethod
    async def list_ratings_for_target(self, target_player_id: UUID) -> Sequence[int]:
        """Return ratings used to recalculate a player's aggregate rating."""
