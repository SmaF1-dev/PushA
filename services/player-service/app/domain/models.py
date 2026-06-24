from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .enums import PlayerStatus, ValorantRank, ValorantRole
from .exceptions import InvalidPlayerError, InvalidProfileError, InvalidReviewError


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp.

    :returns: Current datetime in UTC.
    """
    return datetime.now(UTC)


def _clean_required(value: str, field_name: str, error_type: type[ValueError]) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise error_type(f"{field_name} cannot be empty")
    return cleaned


@dataclass(slots=True)
class Player:
    """Represent a player account independently from persistence.

    :param nickname: Non-empty player display name.
    :param riot_id: Non-empty unique Riot identifier.
    :param id: Stable player UUID.
    :param created_at: Account creation time.
    :param updated_at: Last account modification time.
    :raises InvalidPlayerError: If required text is blank.
    """

    nickname: str
    riot_id: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.nickname = _clean_required(self.nickname, "nickname", InvalidPlayerError)
        self.riot_id = _clean_required(self.riot_id, "riot_id", InvalidPlayerError)

    def rename(self, nickname: str) -> None:
        """Change the player's display name.

        :param nickname: New non-empty nickname.
        :returns: ``None``.
        :raises InvalidPlayerError: If the nickname is blank.
        """
        self.nickname = _clean_required(nickname, "nickname", InvalidPlayerError)
        self.updated_at = utc_now()


@dataclass(slots=True)
class ValorantProfile:
    """Represent a player's Valorant-specific matchmaking data.

    :param player_id: UUID of the profile owner.
    :param region: Non-empty matchmaking region.
    :param current_rank: Current Valorant rank.
    :param main_roles: Non-empty set of preferred roles.
    :param status: Current player availability.
    :param teammate_rating: Aggregate rating between zero and five.
    :param reviews_count: Number of reviews included in the rating.
    :raises InvalidProfileError: If profile invariants are violated.
    """

    player_id: UUID
    region: str
    current_rank: ValorantRank
    main_roles: frozenset[ValorantRole]
    id: UUID = field(default_factory=uuid4)
    status: PlayerStatus = PlayerStatus.OFFLINE
    teammate_rating: float = 0.0
    reviews_count: int = 0
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.region = self._normalize_region(self.region)
        self.main_roles = self._normalize_roles(self.main_roles)

        if not isinstance(self.current_rank, ValorantRank):
            raise InvalidProfileError("current_rank must be a ValorantRank")
        if not isinstance(self.status, PlayerStatus):
            raise InvalidProfileError("status must be a PlayerStatus")
        if self.reviews_count < 0:
            raise InvalidProfileError("reviews_count cannot be negative")
        if not 0 <= self.teammate_rating <= 5:
            raise InvalidProfileError("teammate_rating must be between 0 and 5")
        if self.reviews_count == 0 and self.teammate_rating != 0:
            raise InvalidProfileError("a profile without reviews must have a zero rating")

    @staticmethod
    def _normalize_region(region: str) -> str:
        return _clean_required(region, "region", InvalidProfileError).upper()

    @staticmethod
    def _normalize_roles(roles: Iterable[ValorantRole]) -> frozenset[ValorantRole]:
        normalized = frozenset(roles)
        if not normalized:
            raise InvalidProfileError("at least one main role is required")
        if any(not isinstance(role, ValorantRole) for role in normalized):
            raise InvalidProfileError("main_roles must contain only ValorantRole values")
        return normalized

    def change_status(self, status: PlayerStatus) -> None:
        """Change player availability.

        :param status: New valid player status.
        :returns: ``None``.
        :raises InvalidProfileError: If ``status`` is not a ``PlayerStatus``.
        """
        if not isinstance(status, PlayerStatus):
            raise InvalidProfileError("status must be a PlayerStatus")
        self.status = status
        self.updated_at = utc_now()

    def update_game_details(
        self,
        *,
        region: str | None = None,
        current_rank: ValorantRank | None = None,
        main_roles: Iterable[ValorantRole] | None = None,
    ) -> None:
        """Update supplied Valorant profile fields.

        :param region: Optional new matchmaking region.
        :param current_rank: Optional new Valorant rank.
        :param main_roles: Optional non-empty collection of roles.
        :returns: ``None``.
        :raises InvalidProfileError: If any supplied value is invalid.
        """
        if region is not None:
            self.region = self._normalize_region(region)
        if current_rank is not None:
            if not isinstance(current_rank, ValorantRank):
                raise InvalidProfileError("current_rank must be a ValorantRank")
            self.current_rank = current_rank
        if main_roles is not None:
            self.main_roles = self._normalize_roles(main_roles)
        self.updated_at = utc_now()

    def recalculate_rating(self, ratings: Iterable[int]) -> None:
        """Recalculate aggregate rating from individual reviews.

        :param ratings: Integer ratings from one to five.
        :returns: ``None``.
        :raises InvalidReviewError: If a rating is not an integer from one to five.
        """
        values = list(ratings)
        if any(not isinstance(value, int) for value in values):
            raise InvalidReviewError("review ratings must be integers")
        if any(not 1 <= value <= 5 for value in values):
            raise InvalidReviewError("review rating must be between 1 and 5")

        self.reviews_count = len(values)
        self.teammate_rating = round(sum(values) / len(values), 2) if values else 0.0
        self.updated_at = utc_now()


@dataclass(slots=True)
class TeammateReview:
    """Represent one player's review of another player.

    :param reviewer_id: UUID of the reviewing player.
    :param target_player_id: UUID of the reviewed player.
    :param rating: Integer rating from one to five.
    :param comment: Optional comment; blank text is normalized to ``None``.
    :raises InvalidReviewError: If the review is a self-review or rating is invalid.
    """

    reviewer_id: UUID
    target_player_id: UUID
    rating: int
    comment: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.reviewer_id == self.target_player_id:
            raise InvalidReviewError("a player cannot review themselves")
        if isinstance(self.rating, bool) or not isinstance(self.rating, int):
            raise InvalidReviewError("rating must be an integer")
        if not 1 <= self.rating <= 5:
            raise InvalidReviewError("rating must be between 1 and 5")
        if self.comment is not None:
            cleaned = self.comment.strip()
            self.comment = cleaned or None
