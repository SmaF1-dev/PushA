import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health_router, players_router, profiles_router, reviews_router
from app.api.exception_handlers import register_exception_handlers
from app.config import Settings, get_settings
from app.db import dispose_engine


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


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Manage resources shared by the FastAPI application.

    :param application: Running FastAPI application.
    :yields: Control to FastAPI while the application is serving requests.
    """
    del application
    yield
    await dispose_engine()


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
        lifespan=lifespan,
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

    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
    )
