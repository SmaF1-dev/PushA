from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .enums import PlayerStatus, ValorantRank, ValorantRole
from .exceptions import InvalidPlayerError, InvalidProfileError, InvalidReviewError


def utc_now() -> datetime:
    return datetime.now(UTC)


def _clean_required(value: str, field_name: str, error_type: type[ValueError]) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise error_type(f"{field_name} cannot be empty")
    return cleaned


@dataclass(slots=True)
class Player:
    nickname: str
    riot_id: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.nickname = _clean_required(self.nickname, "nickname", InvalidPlayerError)
        self.riot_id = _clean_required(self.riot_id, "riot_id", InvalidPlayerError)

    def rename(self, nickname: str) -> None:
        self.nickname = _clean_required(nickname, "nickname", InvalidPlayerError)
        self.updated_at = utc_now()


@dataclass(slots=True)
class ValorantProfile:
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
