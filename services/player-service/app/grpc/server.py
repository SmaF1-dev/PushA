import logging

import grpc

from app.config import Settings, get_settings

from .dependencies import PlayerQueryServiceScope, player_query_service_scope
from .generated import valorant_player_service_pb2_grpc as player_pb2_grpc
from .servicer import ValorantPlayerGrpcServicer


logger = logging.getLogger(__name__)


def _format_address(host: str, port: int) -> str:
    """Format an IPv4, hostname, or IPv6 gRPC bind address.

    :param host: Interface or hostname to bind.
    :param port: TCP port, including zero for an ephemeral test port.
    :returns: Address accepted by gRPC.
    """
    formatted_host = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return f"{formatted_host}:{port}"


class PlayerGrpcServer:
    """Own the lifecycle of the asynchronous Player Service gRPC server.

    :param host: Interface or hostname to bind.
    :param port: TCP port; zero requests an ephemeral port for tests.
    :param service_scope: Factory providing a query service for each RPC.
    :raises RuntimeError: If gRPC cannot bind the requested address.
    """

    def __init__(
        self,
        host: str,
        port: int,
        service_scope: PlayerQueryServiceScope = player_query_service_scope,
    ) -> None:
        self._host = host
        self._server = grpc.aio.server()
        player_pb2_grpc.add_ValorantPlayerServiceServicer_to_server(
            ValorantPlayerGrpcServicer(service_scope),
            self._server,
        )
        self._port = self._server.add_insecure_port(_format_address(host, port))
        if self._port == 0:
            raise RuntimeError(f"failed to bind gRPC server to {host}:{port}")

    @property
    def port(self) -> int:
        """Return the actual bound TCP port.

        :returns: Configured or dynamically assigned port.
        """
        return self._port

    @property
    def address(self) -> str:
        """Return the bound address suitable for logging.

        :returns: Host and actual port.
        """
        return _format_address(self._host, self._port)

    async def start(self) -> None:
        """Start accepting gRPC requests.

        :returns: ``None``.
        """
        await self._server.start()
        logger.info("Player Service gRPC server started on %s", self.address)

    async def stop(self, grace: float | None = 5.0) -> None:
        """Stop accepting requests and finish active calls when possible.

        :param grace: Seconds allowed for active RPCs, or ``None`` to wait forever.
        :returns: ``None``.
        """
        await self._server.stop(grace)
        logger.info("Player Service gRPC server stopped")

    async def wait_for_termination(self) -> None:
        """Wait until the server has terminated.

        :returns: ``None``.
        """
        await self._server.wait_for_termination()


def create_grpc_server(
    settings: Settings | None = None,
    service_scope: PlayerQueryServiceScope = player_query_service_scope,
) -> PlayerGrpcServer:
    """Create a configured but not yet started gRPC server.

    :param settings: Explicit settings or cached environment configuration.
    :param service_scope: Factory providing one query service per RPC.
    :returns: Configured Player Service gRPC server.
    """
    current_settings = settings or get_settings()
    return PlayerGrpcServer(
        current_settings.grpc_host,
        current_settings.grpc_port,
        service_scope,
    )
