from collections.abc import Sequence
from uuid import UUID

from app.domain import (
    EligibilityReason,
    EligibilityResult,
    PlayerProfileSnapshot,
    PlayerSelectionCriteria,
)
from app.repositories.interfaces import PlayerQueryRepository


class PlayerQueryService:
    """Coordinate read-only player queries used by other services.

    :param repository: Read repository for joined player/profile projections.
    """

    def __init__(self, repository: PlayerQueryRepository) -> None:
        self._repository = repository

    async def get_profile(self, player_id: UUID) -> PlayerProfileSnapshot | None:
        """Return the matchmaking projection of one player.

        :param player_id: Player UUID.
        :returns: Player projection or ``None`` when absent.
        """
        return await self._repository.get_profile(player_id)

    async def find_players(
        self,
        criteria: PlayerSelectionCriteria,
    ) -> Sequence[PlayerProfileSnapshot]:
        """Return players satisfying matchmaking filters.

        :param criteria: Validated search criteria.
        :returns: Matching player projections.
        """
        return await self._repository.find_players(criteria)

    async def check_eligibility(
        self,
        player_id: UUID,
        criteria: PlayerSelectionCriteria,
    ) -> EligibilityResult:
        """Evaluate one player against matchmaking filters.

        :param player_id: Player UUID to evaluate.
        :param criteria: Validated eligibility criteria.
        :returns: Eligibility flag and stable rejection reasons.
        """
        profile = await self._repository.get_profile(player_id)
        if profile is None:
            return EligibilityResult(
                eligible=False,
                reasons=(EligibilityReason.PLAYER_NOT_FOUND,),
            )

        reasons = criteria.rejection_reasons(profile)
        return EligibilityResult(eligible=not reasons, reasons=reasons)
