import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.api import health_router, players_router, profiles_router, reviews_router
from app.api.exception_handlers import register_exception_handlers
from app.config import Settings, get_settings
from app.db import dispose_engine
from app.grpc import create_grpc_server


OPENAPI_TAGS = [
    {"name": "players", "description": "Player account operations."},
    {"name": "profiles", "description": "Valorant profile operations."},
    {"name": "reviews", "description": "Teammate review operations."},
    {"name": "health", "description": "Service liveness."},
]


def configure_logging(level: str) -> None:
    """Configure process logging from application settings.

    :param level: Standard Python logging level name.
    :returns: ``None``.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def create_lifespan(settings: Settings) -> Lifespan:
    """Create a lifecycle that owns both gRPC and database resources.

    :param settings: Validated application configuration.
    :returns: FastAPI-compatible asynchronous lifespan callable.
    """

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        """Start gRPC beside HTTP and release shared resources on shutdown.

        :param application: Running FastAPI application.
        :yields: Control while both transports are accepting requests.
        """
        grpc_server = create_grpc_server(settings)
        application.state.grpc_server = grpc_server
        try:
            await grpc_server.start()
            yield
        finally:
            await grpc_server.stop()
            await dispose_engine()

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the Player Service HTTP application.

    :param settings: Explicit settings or ``None`` to use cached environment settings.
    :returns: Configured FastAPI application.
    """
    current_settings = settings or get_settings()
    configure_logging(current_settings.log_level)

    application = FastAPI(
        title="Valorant Player Service",
        summary="Player profiles and teammate reviews for Valorant matchmaking",
        description=(
            "Manages player accounts, Valorant profiles, availability statuses, "
            "teammate reviews, and aggregate ratings."
        ),
        version="0.1.0",
        debug=current_settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS,
        lifespan=create_lifespan(current_settings),
    )
    application.state.settings = current_settings

    application.include_router(health_router)
    application.include_router(players_router)
    application.include_router(profiles_router)
    application.include_router(reviews_router)
    register_exception_handlers(application)
    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    runtime_settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=runtime_settings.http_host,
        port=runtime_settings.http_port,
        reload=runtime_settings.debug,
    )
