from collections.abc import Iterable
from uuid import UUID

from app.domain import Player, ValorantProfile, ValorantRank, ValorantRole
from app.repositories.interfaces import PlayerRepository, ProfileRepository

from .exceptions import PlayerNotFoundError, RiotIdAlreadyExistsError
from .transactions import TransactionManager


class PlayerService:
    """Coordinate player-account use cases.

    :param players: Player repository implementation.
    :param profiles: Valorant profile repository implementation.
    :param transaction: Transaction boundary used by write operations.
    """

    def __init__(
        self,
        players: PlayerRepository,
        profiles: ProfileRepository,
        transaction: TransactionManager,
    ) -> None:
        self._players = players
        self._profiles = profiles
        self._transaction = transaction

    async def create_player(
        self,
        *,
        nickname: str,
        riot_id: str,
        region: str,
        current_rank: ValorantRank,
        main_roles: Iterable[ValorantRole],
    ) -> tuple[Player, ValorantProfile]:
        """Create a player and their single Valorant profile atomically.

        :param nickname: Non-empty display name.
        :param riot_id: Globally unique Riot identifier.
        :param region: Player matchmaking region.
        :param current_rank: Current Valorant rank.
        :param main_roles: Non-empty collection of preferred roles.
        :returns: Persisted player and profile.
        :raises RiotIdAlreadyExistsError: If the Riot ID is already registered.
        :raises InvalidPlayerError: If player data violates domain rules.
        :raises InvalidProfileError: If profile data violates domain rules.
        """
        try:
            if await self._players.exists_by_riot_id(riot_id):
                raise RiotIdAlreadyExistsError(riot_id)

            player = Player(nickname=nickname, riot_id=riot_id)
            profile = ValorantProfile(
                player_id=player.id,
                region=region,
                current_rank=current_rank,
                main_roles=frozenset(main_roles),
            )

            persisted_player = await self._players.add(player)
            persisted_profile = await self._profiles.add(profile)
            await self._transaction.commit()
            return persisted_player, persisted_profile
        except Exception:
            await self._transaction.rollback()
            raise

    async def get_player(self, player_id: UUID) -> Player:
        """Return a player by ID.

        :param player_id: Player UUID.
        :returns: Requested player.
        :raises PlayerNotFoundError: If the player does not exist.
        """
        player = await self._players.get_by_id(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id)
        return player
