import unittest
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import grpc

from app.domain import (
    PlayerStatus,
    ValorantRank,
    ValorantRole,
)
from app.grpc.generated import valorant_player_service_pb2 as player_pb2
from app.grpc.generated import valorant_player_service_pb2_grpc as player_pb2_grpc
from app.grpc.server import PlayerGrpcServer
from app.services import PlayerQueryService
from tests.fakes import FakePlayerQueryRepository
from tests.test_player_queries import make_snapshot


def make_service_scope(
        service: PlayerQueryService,
):
    """Build a gRPC dependency scope around a test query service.

    :param service: Query service returned for every test RPC.
    :returns: Async context-manager factory accepted by the servicer.
    """

    @asynccontextmanager
    async def scope() -> AsyncIterator[PlayerQueryService]:
        """Yield the configured in-memory query service.

        :yields: Query service used by one RPC.
        """
        yield service

    return scope


class GrpcApiTests(unittest.IsolatedAsyncioTestCase):
    """Verify the protobuf contract through a real in-process gRPC channel."""

    async def asyncSetUp(self) -> None:
        """Start a gRPC server on an ephemeral local port.

        :returns: ``None``.
        """
        self.matching = make_snapshot()
        self.other = make_snapshot(
            region="NA",
            rank=ValorantRank.SILVER_1,
            status=PlayerStatus.OFFLINE,
            rating=2.0,
            roles=frozenset({ValorantRole.DUELIST}),
        )
        service = PlayerQueryService(
            FakePlayerQueryRepository([self.matching, self.other])
        )
        self.server = PlayerGrpcServer(
            "127.0.0.1",
            0,
            make_service_scope(service),
        )
        await self.server.start()
        self.channel = grpc.aio.insecure_channel(
            f"127.0.0.1:{self.server.port}"
        )
        self.stub = player_pb2_grpc.ValorantPlayerServiceStub(self.channel)

    async def asyncTearDown(self) -> None:
        """Close the channel and stop the ephemeral server.

        :returns: ``None``.
        """
        await self.channel.close()
        await self.server.stop(0)

    async def test_get_existing_and_missing_profile(self) -> None:
        """Honor the protobuf ``exists`` convention for profile lookups."""
        existing = await self.stub.GetValorantProfile(
            player_pb2.GetValorantProfileRequest(
                player_id=str(self.matching.player_id)
            )
        )
        missing = await self.stub.GetValorantProfile(
            player_pb2.GetValorantProfileRequest(
                player_id="00000000-0000-0000-0000-000000000000"
            )
        )

        self.assertTrue(existing.exists)
        self.assertEqual(existing.nickname, self.matching.nickname)
        self.assertEqual(existing.current_rank, "GOLD_2")
        self.assertFalse(missing.exists)

    async def test_find_players_applies_filters(self) -> None:
        """Return only candidates satisfying all request filters."""
        response = await self.stub.FindValorantPlayers(
            player_pb2.FindValorantPlayersRequest(
                excluded_player_id="00000000-0000-0000-0000-000000000000",
                min_rank="GOLD_1",
                max_rank="PLATINUM_3",
                required_player_status="READY_TO_PLAY",
                min_teammate_rating=4.0,
                region="eu",
                required_roles=["CONTROLLER"],
                limit=10,
            )
        )

        self.assertEqual(len(response.candidates), 1)
        self.assertEqual(
            response.candidates[0].player_id,
            str(self.matching.player_id),
        )
        self.assertEqual(response.candidates[0].reviews_count, 10)

    async def test_check_eligibility_returns_stable_reasons(self) -> None:
        """Return all domain rejection codes through protobuf."""
        response = await self.stub.CheckValorantPlayerEligibility(
            player_pb2.CheckValorantPlayerEligibilityRequest(
                player_id=str(self.other.player_id),
                min_rank="GOLD_1",
                max_rank="PLATINUM_3",
                required_player_status="READY_TO_PLAY",
                min_teammate_rating=4.0,
                region="EU",
                required_roles=["CONTROLLER"],
            )
        )

        self.assertFalse(response.eligible)
        self.assertEqual(
            list(response.reasons),
            [
                "RANK_OUT_OF_RANGE",
                "STATUS_MISMATCH",
                "RATING_BELOW_MINIMUM",
                "REGION_MISMATCH",
                "ROLE_MISMATCH",
            ],
        )

    async def test_invalid_request_returns_invalid_argument(self) -> None:
        """Translate malformed protobuf data to ``INVALID_ARGUMENT``."""
        with self.assertRaises(grpc.aio.AioRpcError) as caught:
            await self.stub.GetValorantProfile(
                player_pb2.GetValorantProfileRequest(player_id="not-a-uuid")
            )

        self.assertIs(caught.exception.code(), grpc.StatusCode.INVALID_ARGUMENT)


if __name__ == "__main__":
    unittest.main()
