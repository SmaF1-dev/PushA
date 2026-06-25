from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PlayerModel, ValorantProfileModel
from app.domain import PlayerProfileSnapshot, PlayerSelectionCriteria
from app.repositories.interfaces import PlayerQueryRepository


def _to_snapshot(
    player: PlayerModel,
    profile: ValorantProfileModel,
) -> PlayerProfileSnapshot:
    """Map joined ORM models to a transport-independent read model.

    :param player: Persisted player account.
    :param profile: Persisted Valorant profile.
    :returns: Immutable matchmaking read model.
    """
    return PlayerProfileSnapshot(
        player_id=player.id,
        nickname=player.nickname,
        riot_id=player.riot_id,
        region=profile.region,
        current_rank=profile.current_rank,
        main_roles=frozenset(profile.main_roles),
        status=profile.status,
        teammate_rating=float(profile.teammate_rating),
        reviews_count=profile.reviews_count,
    )


class SqlAlchemyPlayerQueryRepository(PlayerQueryRepository):
    """Read joined player/profile projections through SQLAlchemy.

    :param session: Session used for read operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_profile(self, player_id: UUID) -> PlayerProfileSnapshot | None:
        """Return a player together with their Valorant profile.

        :param player_id: Player UUID.
        :returns: Joined read model or ``None`` when absent.
        """
        statement = (
            select(PlayerModel, ValorantProfileModel)
            .join(
                ValorantProfileModel,
                ValorantProfileModel.player_id == PlayerModel.id,
            )
            .where(PlayerModel.id == player_id)
        )
        row = (await self._session.execute(statement)).one_or_none()
        return _to_snapshot(*row) if row is not None else None

    async def find_players(
        self,
        criteria: PlayerSelectionCriteria,
    ) -> Sequence[PlayerProfileSnapshot]:
        """Find players matching rank, status, rating, region, and roles.

        :param criteria: Validated matchmaking selection criteria.
        :returns: Matching read models ordered by rating and UUID.
        """
        statement = (
            select(PlayerModel, ValorantProfileModel)
            .join(
                ValorantProfileModel,
                ValorantProfileModel.player_id == PlayerModel.id,
            )
            .where(
                ValorantProfileModel.current_rank.in_(criteria.accepted_ranks),
                ValorantProfileModel.status == criteria.required_status,
                ValorantProfileModel.teammate_rating
                >= Decimal(str(criteria.min_teammate_rating)),
                ValorantProfileModel.region == criteria.region,
            )
        )
        if criteria.excluded_player_id is not None:
            statement = statement.where(
                PlayerModel.id != criteria.excluded_player_id
            )
        if criteria.required_roles:
            statement = statement.where(
                ValorantProfileModel.main_roles.overlap(
                    sorted(criteria.required_roles, key=lambda role: role.value)
                )
            )

        statement = statement.order_by(
            ValorantProfileModel.teammate_rating.desc(),
            PlayerModel.id,
        ).limit(criteria.limit)
        rows = (await self._session.execute(statement)).all()
        return [_to_snapshot(player, profile) for player, profile in rows]
