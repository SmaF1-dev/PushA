from collections.abc import Iterable
from uuid import UUID

from app.domain import PlayerStatus, ValorantProfile, ValorantRank, ValorantRole
from app.repositories.interfaces import ProfileRepository

from .exceptions import ProfileNotFoundError
from .transactions import TransactionManager


class ProfileService:
    """Coordinate Valorant-profile use cases.

    :param profiles: Valorant profile repository implementation.
    :param transaction: Transaction boundary used by write operations.
    """

    def __init__(
        self,
        profiles: ProfileRepository,
        transaction: TransactionManager,
    ) -> None:
        self._profiles = profiles
        self._transaction = transaction

    async def get_profile(self, player_id: UUID) -> ValorantProfile:
        """Return the Valorant profile owned by a player.

        :param player_id: Owner player UUID.
        :returns: Requested Valorant profile.
        :raises ProfileNotFoundError: If the profile does not exist.
        """
        profile = await self._profiles.get_by_player_id(player_id)
        if profile is None:
            raise ProfileNotFoundError(player_id)
        return profile

    async def update_profile(
        self,
        player_id: UUID,
        *,
        region: str | None = None,
        current_rank: ValorantRank | None = None,
        main_roles: Iterable[ValorantRole] | None = None,
    ) -> ValorantProfile:
        """Update supplied game-specific profile fields atomically.

        :param player_id: Owner player UUID.
        :param region: Optional new matchmaking region.
        :param current_rank: Optional new Valorant rank.
        :param main_roles: Optional non-empty collection of preferred roles.
        :returns: Updated profile.
        :raises ProfileNotFoundError: If the profile does not exist.
        :raises InvalidProfileError: If supplied data violates domain rules.
        """
        try:
            profile = await self._profiles.get_by_player_id_for_update(player_id)
            if profile is None:
                raise ProfileNotFoundError(player_id)

            profile.update_game_details(
                region=region,
                current_rank=current_rank,
                main_roles=main_roles,
            )
            updated = await self._profiles.update(profile)
            if updated is None:
                raise ProfileNotFoundError(player_id)

            await self._transaction.commit()
            return updated
        except Exception:
            await self._transaction.rollback()
            raise

    async def update_status(
        self, player_id: UUID, status: PlayerStatus
    ) -> ValorantProfile:
        """Update player availability atomically.

        :param player_id: Owner player UUID.
        :param status: New valid player status.
        :returns: Updated profile.
        :raises ProfileNotFoundError: If the profile does not exist.
        :raises InvalidProfileError: If ``status`` is invalid.
        """
        try:
            profile = await self._profiles.get_by_player_id_for_update(player_id)
            if profile is None:
                raise ProfileNotFoundError(player_id)

            profile.change_status(status)
            updated = await self._profiles.update(profile)
            if updated is None:
                raise ProfileNotFoundError(player_id)

            await self._transaction.commit()
            return updated
        except Exception:
            await self._transaction.rollback()
            raise
