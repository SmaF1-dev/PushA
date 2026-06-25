from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def normalize_region(value: str) -> str:
    """Normalize a matchmaking region for domain and database consistency.

    :param value: Region supplied by an API client.
    :returns: Uppercase region value.
    """
    return value.upper()


Nickname = Annotated[str, Field(min_length=1, max_length=100)]
RiotId = Annotated[str, Field(min_length=1, max_length=100)]
Region = Annotated[
    str,
    Field(min_length=1, max_length=32),
    AfterValidator(normalize_region),
]


class ApiSchema(BaseModel):
    """Provide shared validation rules for API schemas.

    Unknown fields are rejected, strings are stripped, and response schemas can
    be constructed from domain entities or ORM-like objects.
    """

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        str_strip_whitespace=True,
    )


class ErrorResponse(ApiSchema):
    """Describe a predictable API error.

    :ivar detail: Human-readable error description.
    """

    detail: str


class ValidationErrorResponse(ErrorResponse):
    """Describe an API validation error with optional structured context.

    :ivar detail: Human-readable validation summary.
    :ivar errors: Structured validation details suitable for clients.
    """

    errors: list[dict[str, Any]] = Field(default_factory=list)


class HealthResponse(ApiSchema):
    """Describe service health.

    :ivar status: Current health status, normally ``ok``.
    :ivar service: Service identifier.
    """

    status: str = "ok"
    service: str = "player-service"
