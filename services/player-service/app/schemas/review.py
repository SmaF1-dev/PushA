from datetime import datetime
from uuid import UUID

from pydantic import Field, StrictInt, field_validator

from .common import ApiSchema


class CreateReviewRequest(ApiSchema):
    """Describe creation of a teammate review.

    The reviewed player is supplied by the endpoint path.

    :ivar reviewer_id: UUID of the player writing the review.
    :ivar rating: Integer rating from one to five.
    :ivar comment: Optional review text.
    """

    reviewer_id: UUID
    rating: StrictInt = Field(ge=1, le=5)
    comment: str | None = None

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        """Normalize blank review comments to ``None``.

        :param value: Optional stripped comment value.
        :returns: Comment text or ``None`` when blank.
        """
        return value or None


class ReviewResponse(ApiSchema):
    """Expose a persisted teammate review.

    :ivar id: Review UUID.
    :ivar reviewer_id: UUID of the reviewing player.
    :ivar target_player_id: UUID of the reviewed player.
    :ivar rating: Integer rating from one to five.
    :ivar comment: Optional review text.
    :ivar created_at: Review creation timestamp.
    """

    id: UUID
    reviewer_id: UUID
    target_player_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None
    created_at: datetime


class ReviewPagination(ApiSchema):
    """Validate query parameters used to paginate reviews.

    :ivar limit: Maximum number of reviews returned per request.
    :ivar offset: Number of reviews skipped from the beginning.
    """

    limit: int = Field(default=100, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ReviewListResponse(ApiSchema):
    """Expose a page of teammate reviews.

    :ivar items: Reviews in the current page.
    :ivar limit: Applied page size.
    :ivar offset: Applied page offset.
    """

    items: list[ReviewResponse]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
