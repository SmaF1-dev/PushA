from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.schemas import (
    CreateReviewRequest,
    ErrorResponse,
    ReviewListResponse,
    ReviewPagination,
    ReviewResponse,
    ValidationErrorResponse,
)

from .dependencies import ReviewServiceDependency


router = APIRouter(prefix="/api/v1/players", tags=["reviews"])
ReviewPaginationDependency = Annotated[ReviewPagination, Depends()]


@router.post(
    "/{target_player_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Player or profile not found"},
        422: {"model": ValidationErrorResponse, "description": "Invalid review"},
    },
)
async def create_review(
    target_player_id: UUID,
    request: CreateReviewRequest,
    service: ReviewServiceDependency,
) -> ReviewResponse:
    """Create a teammate review for a target player.

    :param target_player_id: UUID of the reviewed player.
    :param request: Validated review input.
    :param service: Injected review application service.
    :returns: Created teammate review.
    :raises PlayerNotFoundError: If either player does not exist.
    :raises ProfileNotFoundError: If the target has no profile.
    :raises InvalidReviewError: If domain rules reject the review.
    """
    review = await service.create_review(
        reviewer_id=request.reviewer_id,
        target_player_id=target_player_id,
        rating=request.rating,
        comment=request.comment,
    )
    return ReviewResponse.model_validate(review)


@router.get(
    "/{player_id}/reviews",
    response_model=ReviewListResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Player not found"},
        422: {"model": ValidationErrorResponse, "description": "Invalid query"},
    },
)
async def list_reviews(
    player_id: UUID,
    pagination: ReviewPaginationDependency,
    service: ReviewServiceDependency,
) -> ReviewListResponse:
    """Return a page of reviews received by a player.

    :param player_id: UUID of the reviewed player.
    :param pagination: Validated pagination query.
    :param service: Injected review application service.
    :returns: Requested review page.
    :raises PlayerNotFoundError: If the player does not exist.
    """
    reviews = await service.list_reviews(
        player_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return ReviewListResponse(
        items=[ReviewResponse.model_validate(review) for review in reviews],
        limit=pagination.limit,
        offset=pagination.offset,
    )
