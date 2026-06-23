from abc import ABC, abstractmethod
from uuid import UUID

from app.domain import Player


class PlayerRepository(ABC):
    @abstractmethod
    async def add(self, player: Player) -> Player:
        """Persist and return a player."""

    @abstractmethod
    async def get_by_id(self, player_id: UUID) -> Player | None:
        """Return a player by ID, if it exists."""

    @abstractmethod
    async def get_by_riot_id(self, riot_id: str) -> Player | None:
        """Return a player by Riot ID, if it exists."""

    @abstractmethod
    async def exists_by_riot_id(self, riot_id: str) -> bool:
        """Check whether a Riot ID is already registered."""
