from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ValorantProfileModel
from app.domain import ValorantProfile
from app.repositories.interfaces import ProfileRepository
from app.repositories.mappers import profile_to_domain, profile_to_model


class SqlAlchemyProfileRepository(ProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile: ValorantProfile) -> ValorantProfile:
        model = profile_to_model(profile)
        self._session.add(model)
        await self._session.flush()
        return profile_to_domain(model)

    async def get_by_id(self, profile_id: UUID) -> ValorantProfile | None:
        model = await self._session.get(ValorantProfileModel, profile_id)
        return profile_to_domain(model) if model is not None else None

    async def get_by_player_id(self, player_id: UUID) -> ValorantProfile | None:
        statement = select(ValorantProfileModel).where(
            ValorantProfileModel.player_id == player_id
        )
        model = await self._session.scalar(statement)
        return profile_to_domain(model) if model is not None else None

    async def update(self, profile: ValorantProfile) -> ValorantProfile | None:
        model = await self._session.get(ValorantProfileModel, profile.id)
        if model is None:
            return None

        model.region = profile.region
        model.current_rank = profile.current_rank
        model.main_roles = sorted(profile.main_roles, key=lambda role: role.value)
        model.status = profile.status
        model.teammate_rating = Decimal(str(profile.teammate_rating))
        model.reviews_count = profile.reviews_count
        model.updated_at = profile.updated_at

        await self._session.flush()
        return profile_to_domain(model)
