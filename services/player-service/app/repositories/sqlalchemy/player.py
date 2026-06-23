from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PlayerModel
from app.domain import Player
from app.repositories.interfaces import PlayerRepository
from app.repositories.mappers import player_to_domain, player_to_model


class SqlAlchemyPlayerRepository(PlayerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, player: Player) -> Player:
        model = player_to_model(player)
        self._session.add(model)
        await self._session.flush()
        return player_to_domain(model)

    async def get_by_id(self, player_id: UUID) -> Player | None:
        model = await self._session.get(PlayerModel, player_id)
        return player_to_domain(model) if model is not None else None

    async def get_by_riot_id(self, riot_id: str) -> Player | None:
        statement = select(PlayerModel).where(PlayerModel.riot_id == riot_id)
        model = await self._session.scalar(statement)
        return player_to_domain(model) if model is not None else None

    async def exists_by_riot_id(self, riot_id: str) -> bool:
        statement = select(exists().where(PlayerModel.riot_id == riot_id))
        return bool(await self._session.scalar(statement))
