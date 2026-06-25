from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.domain import PlayerProfileSnapshot, PlayerSelectionCriteria


class PlayerQueryRepository(ABC):
    """Define read operations required by matchmaking integrations."""

    @abstractmethod
    async def get_profile(self, player_id: UUID) -> PlayerProfileSnapshot | None:
        """Return a joined player/profile read model.

        :param player_id: Player UUID.
        :returns: Read model or ``None`` when the player/profile is absent.
        """

    @abstractmethod
    async def find_players(
        self,
        criteria: PlayerSelectionCriteria,
    ) -> Sequence[PlayerProfileSnapshot]:
        """Find player/profile read models satisfying selection criteria.

        :param criteria: Validated matchmaking filters.
        :returns: Matching players in deterministic order.
        """
