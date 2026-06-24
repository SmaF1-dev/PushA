from uuid import UUID

from fastapi import APIRouter

from app.schemas import (
    ErrorResponse,
    UpdatePlayerStatusRequest,
    UpdateValorantProfileRequest,
    ValidationErrorResponse,
    ValorantProfileResponse,
)

from .dependencies import ProfileServiceDependency


router = APIRouter(prefix="/api/v1/players", tags=["profiles"])


@router.patch(
    "/{player_id}/valorant-profile",
    response_model=ValorantProfileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Profile not found"},
        422: {"model": ValidationErrorResponse, "description": "Invalid profile data"},
    },
)
async def update_valorant_profile(
    player_id: UUID,
    request: UpdateValorantProfileRequest,
    service: ProfileServiceDependency,
) -> ValorantProfileResponse:
    """Partially update game-specific profile data.

    :param player_id: UUID of the profile owner.
    :param request: Validated fields to update.
    :param service: Injected profile application service.
    :returns: Updated Valorant profile.
    :raises ProfileNotFoundError: If the profile does not exist.
    :raises InvalidProfileError: If domain rules reject the update.
    """
    profile = await service.update_profile(
        player_id,
        region=request.region,
        current_rank=request.current_rank,
        main_roles=request.main_roles,
    )
    return ValorantProfileResponse.model_validate(profile)


@router.patch(
    "/{player_id}/status",
    response_model=ValorantProfileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Profile not found"},
        422: {"model": ValidationErrorResponse, "description": "Invalid status"},
    },
)
async def update_player_status(
    player_id: UUID,
    request: UpdatePlayerStatusRequest,
    service: ProfileServiceDependency,
) -> ValorantProfileResponse:
    """Update player availability.

    :param player_id: UUID of the profile owner.
    :param request: Validated status update.
    :param service: Injected profile application service.
    :returns: Updated Valorant profile.
    :raises ProfileNotFoundError: If the profile does not exist.
    :raises InvalidProfileError: If domain rules reject the status.
    """
    profile = await service.update_status(player_id, request.status)
    return ValorantProfileResponse.model_validate(profile)
