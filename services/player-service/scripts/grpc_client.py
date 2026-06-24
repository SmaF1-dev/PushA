import argparse
import asyncio
from uuid import UUID, uuid5

import grpc
from google.protobuf.json_format import MessageToJson

from app.grpc.generated import valorant_player_service_pb2 as player_pb2
from app.grpc.generated import valorant_player_service_pb2_grpc as player_pb2_grpc


SEED_NAMESPACE = UUID("897bdd9a-0655-4cd0-babb-5cb8ab74f092")
DEFAULT_PLAYER_ID = str(uuid5(SEED_NAMESPACE, "player-0"))


def print_response(title: str, message) -> None:
    """Print a protobuf response as readable JSON.

    :param title: Heading identifying the RPC.
    :param message: Protobuf message returned by the server.
    :returns: ``None``.
    """
    print(f"\n=== {title} ===")
    print(
        MessageToJson(
            message,
            preserving_proto_field_name=True,
            indent=2,
            always_print_fields_with_no_presence=True,
        )
    )


async def call_get_profile(
    stub: player_pb2_grpc.ValorantPlayerServiceStub,
    arguments: argparse.Namespace,
) -> None:
    """Call ``GetValorantProfile`` and print its response.

    :param stub: Generated asynchronous-compatible gRPC client.
    :param arguments: Parsed client settings.
    :returns: ``None``.
    """
    response = await stub.GetValorantProfile(
        player_pb2.GetValorantProfileRequest(player_id=arguments.player_id),
        timeout=arguments.timeout,
    )
    print_response("GetValorantProfile", response)


async def call_find_players(
    stub: player_pb2_grpc.ValorantPlayerServiceStub,
    arguments: argparse.Namespace,
) -> None:
    """Call ``FindValorantPlayers`` with matchmaking-style filters.

    :param stub: Generated asynchronous-compatible gRPC client.
    :param arguments: Parsed client settings and filters.
    :returns: ``None``.
    """
    response = await stub.FindValorantPlayers(
        player_pb2.FindValorantPlayersRequest(
            excluded_player_id=arguments.player_id,
            min_rank=arguments.min_rank,
            max_rank=arguments.max_rank,
            required_player_status=arguments.status,
            min_teammate_rating=arguments.min_rating,
            region=arguments.region,
            required_roles=arguments.roles,
            limit=arguments.limit,
        ),
        timeout=arguments.timeout,
    )
    print_response("FindValorantPlayers", response)


async def call_check_eligibility(
    stub: player_pb2_grpc.ValorantPlayerServiceStub,
    arguments: argparse.Namespace,
) -> None:
    """Call ``CheckValorantPlayerEligibility`` and print its response.

    :param stub: Generated asynchronous-compatible gRPC client.
    :param arguments: Parsed client settings and filters.
    :returns: ``None``.
    """
    response = await stub.CheckValorantPlayerEligibility(
        player_pb2.CheckValorantPlayerEligibilityRequest(
            player_id=arguments.player_id,
            min_rank=arguments.min_rank,
            max_rank=arguments.max_rank,
            required_player_status=arguments.status,
            min_teammate_rating=arguments.min_rating,
            region=arguments.region,
            required_roles=arguments.roles,
        ),
        timeout=arguments.timeout,
    )
    print_response("CheckValorantPlayerEligibility", response)


def parse_arguments() -> argparse.Namespace:
    """Parse gRPC connection settings, RPC selection, and filters.

    :returns: Parsed client arguments.
    """
    parser = argparse.ArgumentParser(
        description="Call the Player Service gRPC API like matchmaking-service",
    )
    parser.add_argument("--address", default="localhost:50051")
    parser.add_argument(
        "--rpc",
        choices=("all", "get", "find", "check"),
        default="all",
    )
    parser.add_argument("--player-id", default=DEFAULT_PLAYER_ID)
    parser.add_argument("--min-rank", default="GOLD_1")
    parser.add_argument("--max-rank", default="PLATINUM_3")
    parser.add_argument("--status", default="READY_TO_PLAY")
    parser.add_argument("--min-rating", type=float, default=4.0)
    parser.add_argument("--region", default="EU")
    parser.add_argument("--roles", nargs="*", default=["CONTROLLER"])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser.parse_args()


async def async_main(arguments: argparse.Namespace) -> int:
    """Connect to Player Service and invoke selected RPC methods.

    :param arguments: Parsed connection settings and request values.
    :returns: Process exit code: zero on success, one on RPC failure.
    """
    try:
        async with grpc.aio.insecure_channel(arguments.address) as channel:
            await asyncio.wait_for(
                channel.channel_ready(),
                timeout=arguments.timeout,
            )
            stub = player_pb2_grpc.ValorantPlayerServiceStub(channel)

            if arguments.rpc in {"all", "get"}:
                await call_get_profile(stub, arguments)
            if arguments.rpc in {"all", "find"}:
                await call_find_players(stub, arguments)
            if arguments.rpc in {"all", "check"}:
                await call_check_eligibility(stub, arguments)
        return 0
    except TimeoutError:
        print(f"Cannot connect to gRPC server at {arguments.address}")
        return 1
    except grpc.aio.AioRpcError as error:
        print(f"gRPC error: {error.code().name}: {error.details()}")
        return 1


def main() -> None:
    """Run the asynchronous gRPC client command.

    :returns: ``None``.
    """
    raise SystemExit(asyncio.run(async_main(parse_arguments())))


if __name__ == "__main__":
    main()
