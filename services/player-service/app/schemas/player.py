from datetime import datetime
from uuid import UUID

from app.domain import ValorantRank

from .common import ApiSchema, Nickname, Region, RiotId
from .profile import MainRoles, ValorantProfileResponse


class CreatePlayerRequest(ApiSchema):
    """Describe creation of a player and their initial Valorant profile.

    :ivar nickname: Non-empty player display name.
    :ivar riot_id: Globally unique Riot identifier.
    :ivar region: Initial matchmaking region.
    :ivar current_rank: Initial Valorant rank.
    :ivar main_roles: Non-empty set of preferred roles.
    """

    nickname: Nickname
    riot_id: RiotId
    region: Region
    current_rank: ValorantRank
    main_roles: MainRoles


class PlayerResponse(ApiSchema):
    """Expose a persisted player account.

    :ivar id: Player UUID.
    :ivar nickname: Player display name.
    :ivar riot_id: Unique Riot identifier.
    :ivar created_at: Account creation timestamp.
    :ivar updated_at: Last modification timestamp.
    """

    id: UUID
    nickname: str
    riot_id: str
    created_at: datetime
    updated_at: datetime


class PlayerDetailsResponse(ApiSchema):
    """Expose a player together with their Valorant profile.

    :ivar player: Player account data.
    :ivar valorant_profile: Valorant-specific profile data.
    """

    player: PlayerResponse
    valorant_profile: ValorantProfileResponse
