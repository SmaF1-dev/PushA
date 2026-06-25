from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from app.domain import PlayerStatus, ValorantRank, ValorantRole

from .common import ApiSchema, Region


MainRoles = Annotated[frozenset[ValorantRole], Field(min_length=1)]


class UpdateValorantProfileRequest(ApiSchema):
    """Describe a partial update of game-specific profile data.

    :ivar region: Optional new matchmaking region.
    :ivar current_rank: Optional new Valorant rank.
    :ivar main_roles: Optional non-empty set of preferred roles.
    """

    region: Region | None = None
    current_rank: ValorantRank | None = None
    main_roles: MainRoles | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> Self:
        """Require at least one field in a PATCH request.

        :returns: Validated request instance.
        :raises ValueError: If the request contains no profile changes.
        """
        if (
            self.region is None
            and self.current_rank is None
            and self.main_roles is None
        ):
            raise ValueError("at least one profile field must be provided")
        return self


class UpdatePlayerStatusRequest(ApiSchema):
    """Describe an availability-status update.

    :ivar status: New player availability status.
    """

    status: PlayerStatus


class ValorantProfileResponse(ApiSchema):
    """Expose a player's persisted Valorant profile.

    :ivar id: Profile UUID.
    :ivar player_id: UUID of the profile owner.
    :ivar region: Matchmaking region.
    :ivar current_rank: Current Valorant rank.
    :ivar main_roles: Preferred Valorant roles.
    :ivar status: Current availability status.
    :ivar teammate_rating: Aggregate teammate rating from zero to five.
    :ivar reviews_count: Number of reviews included in the rating.
    :ivar created_at: Profile creation timestamp.
    :ivar updated_at: Last modification timestamp.
    """

    id: UUID
    player_id: UUID
    region: Region
    current_rank: ValorantRank
    main_roles: MainRoles
    status: PlayerStatus
    teammate_rating: float = Field(ge=0, le=5)
    reviews_count: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
