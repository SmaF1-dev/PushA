from app.domain import PlayerProfileSnapshot

from .generated import valorant_player_service_pb2 as player_pb2


def to_profile_response(
    profile: PlayerProfileSnapshot,
) -> player_pb2.GetValorantProfileResponse:
    """Map a player read model to the profile protobuf response.

    :param profile: Transport-independent player/profile projection.
    :returns: Populated protobuf response with ``exists`` set to true.
    """
    return player_pb2.GetValorantProfileResponse(
        exists=True,
        player_id=str(profile.player_id),
        nickname=profile.nickname,
        riot_id=profile.riot_id,
        region=profile.region,
        current_rank=profile.current_rank.value,
        main_roles=sorted(role.value for role in profile.main_roles),
        status=profile.status.value,
        teammate_rating=profile.teammate_rating,
        reviews_count=profile.reviews_count,
    )


def to_candidate(
    profile: PlayerProfileSnapshot,
) -> player_pb2.ValorantPlayerCandidate:
    """Map a player read model to a matchmaking candidate message.

    :param profile: Transport-independent player/profile projection.
    :returns: Populated candidate protobuf message.
    """
    return player_pb2.ValorantPlayerCandidate(
        player_id=str(profile.player_id),
        nickname=profile.nickname,
        riot_id=profile.riot_id,
        region=profile.region,
        current_rank=profile.current_rank.value,
        main_roles=sorted(role.value for role in profile.main_roles),
        status=profile.status.value,
        teammate_rating=profile.teammate_rating,
        reviews_count=profile.reviews_count,
    )
