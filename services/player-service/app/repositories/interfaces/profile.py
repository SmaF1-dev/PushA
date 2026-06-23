from abc import ABC, abstractmethod
from uuid import UUID

from app.domain import ValorantProfile


class ProfileRepository(ABC):
    @abstractmethod
    async def add(self, profile: ValorantProfile) -> ValorantProfile:
        """Persist and return a Valorant profile."""

    @abstractmethod
    async def get_by_id(self, profile_id: UUID) -> ValorantProfile | None:
        """Return a profile by ID, if it exists."""

    @abstractmethod
    async def get_by_player_id(self, player_id: UUID) -> ValorantProfile | None:
        """Return the one Valorant profile owned by a player."""

    @abstractmethod
    async def update(self, profile: ValorantProfile) -> ValorantProfile | None:
        """Update an existing profile, returning None when it is absent."""
