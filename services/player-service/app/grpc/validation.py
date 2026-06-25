from enum import Enum
from typing import TypeVar
from uuid import UUID

from app.domain import (
    PlayerSelectionCriteria,
    PlayerStatus,
    ValorantRank,
    ValorantRole,
)


EnumType = TypeVar("EnumType", bound=Enum)


class GrpcRequestError(ValueError):
    """Report malformed or semantically invalid gRPC request data."""


def parse_uuid(value: str, field_name: str) -> UUID:
    """Parse a required UUID string.

    :param value: Raw protobuf string value.
    :param field_name: Field name included in validation messages.
    :returns: Parsed UUID.
    :raises GrpcRequestError: If the value is empty or not a UUID.
    """
    try:
        return UUID(value)
    except (TypeError, ValueError) as error:
        raise GrpcRequestError(f"{field_name} must be a valid UUID") from error


def parse_enum(
    enum_type: type[EnumType],
    value: str,
    field_name: str,
) -> EnumType:
    """Parse a protobuf string into a domain enum.

    :param enum_type: Domain enum class to construct.
    :param value: Raw protobuf string value.
    :param field_name: Field name included in validation messages.
    :returns: Parsed domain enum member.
    :raises GrpcRequestError: If the value is not supported.
    """
    try:
        return enum_type(value)
    except ValueError as error:
        raise GrpcRequestError(f"{field_name} has an unsupported value") from error


def build_selection_criteria(
    *,
    min_rank: str,
    max_rank: str,
    required_player_status: str,
    min_teammate_rating: float,
    region: str,
    required_roles: list[str],
    excluded_player_id: str | None = None,
    limit: int = 100,
) -> PlayerSelectionCriteria:
    """Convert primitive protobuf fields into validated domain criteria.

    :param min_rank: Lowest accepted rank string.
    :param max_rank: Highest accepted rank string.
    :param required_player_status: Required player-status string.
    :param min_teammate_rating: Lowest accepted aggregate rating.
    :param region: Required matchmaking region.
    :param required_roles: Role strings of which at least one must match.
    :param excluded_player_id: Optional player UUID excluded from results.
    :param limit: Maximum number of results.
    :returns: Validated transport-independent selection criteria.
    :raises GrpcRequestError: If a UUID, enum, or role is invalid.
    :raises InvalidPlayerQueryError: If criteria violate domain rules.
    """
    parsed_roles = frozenset(
        parse_enum(ValorantRole, role, "required_roles")
        for role in required_roles
    )
    parsed_excluded_id = (
        parse_uuid(excluded_player_id, "excluded_player_id")
        if excluded_player_id is not None
        else None
    )
    return PlayerSelectionCriteria(
        min_rank=parse_enum(ValorantRank, min_rank, "min_rank"),
        max_rank=parse_enum(ValorantRank, max_rank, "max_rank"),
        required_status=parse_enum(
            PlayerStatus,
            required_player_status,
            "required_player_status",
        ),
        min_teammate_rating=min_teammate_rating,
        region=region,
        required_roles=parsed_roles,
        excluded_player_id=parsed_excluded_id,
        limit=limit,
    )
