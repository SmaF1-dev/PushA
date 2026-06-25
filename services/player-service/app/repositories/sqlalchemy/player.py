from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PlayerModel
from app.db.integrity import RIOT_ID_UNIQUE_CONSTRAINT, find_constraint_name
from app.domain import Player
from app.repositories.exceptions import DuplicateRiotIdError
from app.repositories.interfaces import PlayerRepository
from app.repositories.mappers import player_to_domain, player_to_model


class SqlAlchemyPlayerRepository(PlayerRepository):
    """Persist players through an asynchronous SQLAlchemy session.

    :param session: Session used for all repository operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, player: Player) -> Player:
        """Persist a player without committing the transaction.

        :param player: Domain player to persist.
        :returns: Persisted player.
        :raises DuplicateRiotIdError: If the Riot ID uniqueness constraint is violated.
        :raises sqlalchemy.exc.IntegrityError: If a database constraint is violated.
        """
        model = player_to_model(player)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as error:
            if find_constraint_name(error) == RIOT_ID_UNIQUE_CONSTRAINT:
                raise DuplicateRiotIdError(player.riot_id) from error
            raise
        return player_to_domain(model)

    async def get_by_id(self, player_id: UUID) -> Player | None:
        """Find a player by ID.

        :param player_id: Player UUID.
        :returns: Player or ``None`` when absent.
        """
        model = await self._session.get(PlayerModel, player_id)
        return player_to_domain(model) if model is not None else None

    async def get_by_riot_id(self, riot_id: str) -> Player | None:
        """Find a player by Riot ID.

        :param riot_id: Exact Riot identifier.
        :returns: Player or ``None`` when absent.
        """
        statement = select(PlayerModel).where(PlayerModel.riot_id == riot_id)
        model = await self._session.scalar(statement)
        return player_to_domain(model) if model is not None else None

    async def exists_by_riot_id(self, riot_id: str) -> bool:
        """Check whether a Riot ID is registered.

        :param riot_id: Exact Riot identifier.
        :returns: ``True`` when the Riot ID exists.
        """
        statement = select(exists().where(PlayerModel.riot_id == riot_id))
        return bool(await self._session.scalar(statement))
