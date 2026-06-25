from abc import ABC, abstractmethod
from uuid import UUID

from app.domain import ValorantProfile


class ProfileRepository(ABC):
    """Define persistence operations required for Valorant profiles."""

    @abstractmethod
    async def add(self, profile: ValorantProfile) -> ValorantProfile:
        """Persist a Valorant profile.

        :param profile: Domain profile to persist.
        :returns: Persisted profile.
        """

    @abstractmethod
    async def get_by_id(self, profile_id: UUID) -> ValorantProfile | None:
        """Find a profile by ID.

        :param profile_id: Profile UUID.
        :returns: Profile or ``None`` when absent.
        """

    @abstractmethod
    async def get_by_player_id(self, player_id: UUID) -> ValorantProfile | None:
        """Find the one Valorant profile owned by a player.

        :param player_id: Owner player UUID.
        :returns: Profile or ``None`` when absent.
        """

    @abstractmethod
    async def get_by_player_id_for_update(
        self, player_id: UUID
    ) -> ValorantProfile | None:
        """Find and lock a player's profile for an update.

        :param player_id: Owner player UUID.
        :returns: Locked profile or ``None`` when absent.
        """

    @abstractmethod
    async def update(self, profile: ValorantProfile) -> ValorantProfile | None:
        """Update an existing profile.

        :param profile: Domain profile containing the new state.
        :returns: Updated profile or ``None`` when absent.
        """
