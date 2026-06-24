import logging

import grpc

from app.domain import DomainError

from .dependencies import PlayerQueryServiceScope, player_query_service_scope
from .generated import valorant_player_service_pb2 as player_pb2
from .generated import valorant_player_service_pb2_grpc as player_pb2_grpc
from .mappers import to_candidate, to_profile_response
from .validation import GrpcRequestError, build_selection_criteria, parse_uuid


logger = logging.getLogger(__name__)


class ValorantPlayerGrpcServicer(
    player_pb2_grpc.ValorantPlayerServiceServicer
):
    """Implement the matchmaking-facing Valorant player gRPC contract.

    :param service_scope: Factory providing one query service per RPC.
    """

    def __init__(
        self,
        service_scope: PlayerQueryServiceScope = player_query_service_scope,
    ) -> None:
        self._service_scope = service_scope

    async def GetValorantProfile(
        self,
        request: player_pb2.GetValorantProfileRequest,
        context: grpc.aio.ServicerContext,
    ) -> player_pb2.GetValorantProfileResponse:
        """Return one player/profile projection when it exists.

        :param request: Request containing the player UUID.
        :param context: Active gRPC request context.
        :returns: Profile response; ``exists`` is false when absent.
        """
        try:
            player_id = parse_uuid(request.player_id, "player_id")
            async with self._service_scope() as service:
                profile = await service.get_profile(player_id)
            if profile is None:
                return player_pb2.GetValorantProfileResponse(exists=False)
            return to_profile_response(profile)
        except (GrpcRequestError, DomainError) as error:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(error))
        except Exception as error:
            await self._abort_internal(context, error)

    async def FindValorantPlayers(
        self,
        request: player_pb2.FindValorantPlayersRequest,
        context: grpc.aio.ServicerContext,
    ) -> player_pb2.FindValorantPlayersResponse:
        """Find players satisfying all matchmaking filters.

        :param request: Matchmaking filter request.
        :param context: Active gRPC request context.
        :returns: Candidate messages in deterministic repository order.
        """
        try:
            criteria = build_selection_criteria(
                excluded_player_id=request.excluded_player_id,
                min_rank=request.min_rank,
                max_rank=request.max_rank,
                required_player_status=request.required_player_status,
                min_teammate_rating=request.min_teammate_rating,
                region=request.region,
                required_roles=list(request.required_roles),
                limit=request.limit or 100,
            )
            async with self._service_scope() as service:
                profiles = await service.find_players(criteria)
            return player_pb2.FindValorantPlayersResponse(
                candidates=[to_candidate(profile) for profile in profiles]
            )
        except (GrpcRequestError, DomainError) as error:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(error))
        except Exception as error:
            await self._abort_internal(context, error)

    async def CheckValorantPlayerEligibility(
        self,
        request: player_pb2.CheckValorantPlayerEligibilityRequest,
        context: grpc.aio.ServicerContext,
    ) -> player_pb2.CheckValorantPlayerEligibilityResponse:
        """Evaluate one player against matchmaking filters.

        :param request: Player UUID and eligibility filters.
        :param context: Active gRPC request context.
        :returns: Eligibility flag and stable rejection reason codes.
        """
        try:
            player_id = parse_uuid(request.player_id, "player_id")
            criteria = build_selection_criteria(
                min_rank=request.min_rank,
                max_rank=request.max_rank,
                required_player_status=request.required_player_status,
                min_teammate_rating=request.min_teammate_rating,
                region=request.region,
                required_roles=list(request.required_roles),
            )
            async with self._service_scope() as service:
                result = await service.check_eligibility(player_id, criteria)
            return player_pb2.CheckValorantPlayerEligibilityResponse(
                eligible=result.eligible,
                reasons=[reason.value for reason in result.reasons],
            )
        except (GrpcRequestError, DomainError) as error:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(error))
        except Exception as error:
            await self._abort_internal(context, error)

    @staticmethod
    async def _abort_internal(
        context: grpc.aio.ServicerContext,
        error: Exception,
    ) -> None:
        """Log an unexpected failure and return a safe gRPC error.

        :param context: Active gRPC request context.
        :param error: Unexpected application or persistence error.
        :returns: Never returns because ``context.abort`` terminates the RPC.
        """
        logger.exception("Unhandled gRPC request failure", exc_info=error)
        await context.abort(grpc.StatusCode.INTERNAL, "internal server error")
