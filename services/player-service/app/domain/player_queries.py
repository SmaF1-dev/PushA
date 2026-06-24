from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from .enums import PlayerStatus, ValorantRank, ValorantRole
from .exceptions import InvalidPlayerQueryError


class EligibilityReason(StrEnum):
    """Stable reason codes returned by player eligibility checks."""

    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    RANK_OUT_OF_RANGE = "RANK_OUT_OF_RANGE"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    RATING_BELOW_MINIMUM = "RATING_BELOW_MINIMUM"
    REGION_MISMATCH = "REGION_MISMATCH"
    ROLE_MISMATCH = "ROLE_MISMATCH"


@dataclass(frozen=True, slots=True)
class PlayerProfileSnapshot:
    """Represent the player data exposed to matchmaking queries.

    :param player_id: Stable player UUID.
    :param nickname: Player display name.
    :param riot_id: Unique Riot identifier.
    :param region: Normalized matchmaking region.
    :param current_rank: Current Valorant rank.
    :param main_roles: Preferred Valorant roles.
    :param status: Current availability status.
    :param teammate_rating: Aggregate teammate rating.
    :param reviews_count: Number of reviews in the aggregate.
    """

    player_id: UUID
    nickname: str
    riot_id: str
    region: str
    current_rank: ValorantRank
    main_roles: frozenset[ValorantRole]
    status: PlayerStatus
    teammate_rating: float
    reviews_count: int


@dataclass(frozen=True, slots=True)
class PlayerSelectionCriteria:
    """Describe filters shared by search and eligibility use cases.

    :param min_rank: Lowest accepted Valorant rank.
    :param max_rank: Highest accepted Valorant rank.
    :param required_status: Required availability status.
    :param min_teammate_rating: Lowest accepted aggregate rating.
    :param region: Required matchmaking region.
    :param required_roles: Roles of which at least one must match.
    :param excluded_player_id: Optional player UUID excluded from search.
    :param limit: Maximum number of search results.
    :raises InvalidPlayerQueryError: If criteria are inconsistent or invalid.
    """

    min_rank: ValorantRank
    max_rank: ValorantRank
    required_status: PlayerStatus
    min_teammate_rating: float
    region: str
    required_roles: frozenset[ValorantRole] = frozenset()
    excluded_player_id: UUID | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        """Normalize and validate selection criteria.

        :returns: ``None``.
        :raises InvalidPlayerQueryError: If any criterion is invalid.
        """
        if not isinstance(self.min_rank, ValorantRank):
            raise InvalidPlayerQueryError("min_rank must be a ValorantRank")
        if not isinstance(self.max_rank, ValorantRank):
            raise InvalidPlayerQueryError("max_rank must be a ValorantRank")
        if self.min_rank.order > self.max_rank.order:
            raise InvalidPlayerQueryError("min_rank cannot be higher than max_rank")
        if not isinstance(self.required_status, PlayerStatus):
            raise InvalidPlayerQueryError("required_status must be a PlayerStatus")
        if not 0 <= self.min_teammate_rating <= 5:
            raise InvalidPlayerQueryError(
                "min_teammate_rating must be between 0 and 5"
            )

        normalized_region = self.region.strip().upper()
        if not normalized_region:
            raise InvalidPlayerQueryError("region cannot be empty")
        object.__setattr__(self, "region", normalized_region)

        normalized_roles = frozenset(self.required_roles)
        if any(not isinstance(role, ValorantRole) for role in normalized_roles):
            raise InvalidPlayerQueryError(
                "required_roles must contain only ValorantRole values"
            )
        object.__setattr__(self, "required_roles", normalized_roles)

        if isinstance(self.limit, bool) or not isinstance(self.limit, int):
            raise InvalidPlayerQueryError("limit must be an integer")
        if not 1 <= self.limit <= 100:
            raise InvalidPlayerQueryError("limit must be between 1 and 100")

    @property
    def accepted_ranks(self) -> tuple[ValorantRank, ...]:
        """Return every rank contained in the inclusive range.

        :returns: Ordered accepted ranks.
        """
        return tuple(
            rank
            for rank in ValorantRank
            if self.min_rank.order <= rank.order <= self.max_rank.order
        )

    def rejection_reasons(
        self,
        profile: PlayerProfileSnapshot,
    ) -> tuple[EligibilityReason, ...]:
        """Explain why a player does not satisfy these criteria.

        :param profile: Player/profile read model to evaluate.
        :returns: Stable rejection codes; empty when the player is eligible.
        """
        reasons: list[EligibilityReason] = []
        if profile.current_rank not in self.accepted_ranks:
            reasons.append(EligibilityReason.RANK_OUT_OF_RANGE)
        if profile.status is not self.required_status:
            reasons.append(EligibilityReason.STATUS_MISMATCH)
        if profile.teammate_rating < self.min_teammate_rating:
            reasons.append(EligibilityReason.RATING_BELOW_MINIMUM)
        if profile.region != self.region:
            reasons.append(EligibilityReason.REGION_MISMATCH)
        if self.required_roles and self.required_roles.isdisjoint(profile.main_roles):
            reasons.append(EligibilityReason.ROLE_MISMATCH)
        return tuple(reasons)

    def matches(self, profile: PlayerProfileSnapshot) -> bool:
        """Check whether a player satisfies every criterion.

        :param profile: Player/profile read model to evaluate.
        :returns: ``True`` when the player is accepted and not excluded.
        """
        if self.excluded_player_id == profile.player_id:
            return False
        return not self.rejection_reasons(profile)


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    """Describe the result of one eligibility check.

    :param eligible: Whether the player satisfies every criterion.
    :param reasons: Stable rejection reason codes.
    """

    eligible: bool
    reasons: tuple[EligibilityReason, ...] = ()
