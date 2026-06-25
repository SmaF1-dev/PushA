from uuid import UUID

from fastapi import APIRouter, status

from app.schemas import (
    CreatePlayerRequest,
    ErrorResponse,
    PlayerDetailsResponse,
    PlayerResponse,
    ValidationErrorResponse,
    ValorantProfileResponse,
)

from .dependencies import PlayerServiceDependency, ProfileServiceDependency


router = APIRouter(prefix="/api/v1/players", tags=["players"])


@router.post(
    "",
    response_model=PlayerDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Riot ID already exists"},
        422: {"model": ValidationErrorResponse, "description": "Invalid player data"},
    },
)
async def create_player(
    request: CreatePlayerRequest,
    service: PlayerServiceDependency,
) -> PlayerDetailsResponse:
    """Create a player together with their initial Valorant profile.

    :param request: Validated player and profile input.
    :param service: Injected player application service.
    :returns: Created player and Valorant profile.
    :raises RiotIdAlreadyExistsError: If the Riot ID is already registered.
    :raises DomainError: If domain invariants reject the input.
    """
    player, profile = await service.create_player(
        nickname=request.nickname,
        riot_id=request.riot_id,
        region=request.region,
        current_rank=request.current_rank,
        main_roles=request.main_roles,
    )
    return PlayerDetailsResponse(
        player=PlayerResponse.model_validate(player),
        valorant_profile=ValorantProfileResponse.model_validate(profile),
    )


@router.get(
    "/{player_id}",
    response_model=PlayerDetailsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Player or profile not found"},
        422: {"model": ValidationErrorResponse, "description": "Invalid player ID"},
    },
)
async def get_player(
    player_id: UUID,
    player_service: PlayerServiceDependency,
    profile_service: ProfileServiceDependency,
) -> PlayerDetailsResponse:
    """Return a player together with their Valorant profile.

    :param player_id: UUID of the requested player.
    :param player_service: Injected player application service.
    :param profile_service: Injected profile application service.
    :returns: Player and Valorant profile.
    :raises PlayerNotFoundError: If the player does not exist.
    :raises ProfileNotFoundError: If the player has no Valorant profile.
    """
    player = await player_service.get_player(player_id)
    profile = await profile_service.get_profile(player_id)
    return PlayerDetailsResponse(
        player=PlayerResponse.model_validate(player),
        valorant_profile=ValorantProfileResponse.model_validate(profile),
    )
