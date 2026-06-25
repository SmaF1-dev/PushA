from abc import ABC, abstractmethod
from uuid import UUID

from app.domain import Player


class PlayerRepository(ABC):
    """Define persistence operations required for player accounts."""

    @abstractmethod
    async def add(self, player: Player) -> Player:
        """Persist a player.

        :param player: Domain player to persist.
        :returns: Persisted player.
        """

    @abstractmethod
    async def get_by_id(self, player_id: UUID) -> Player | None:
        """Find a player by ID.

        :param player_id: Player UUID.
        :returns: Player or ``None`` when absent.
        """

    @abstractmethod
    async def get_by_riot_id(self, riot_id: str) -> Player | None:
        """Find a player by Riot ID.

        :param riot_id: Exact Riot identifier.
        :returns: Player or ``None`` when absent.
        """

    @abstractmethod
    async def exists_by_riot_id(self, riot_id: str) -> bool:
        """Check whether a Riot ID is registered.

        :param riot_id: Exact Riot identifier.
        :returns: ``True`` when the Riot ID exists.
        """
