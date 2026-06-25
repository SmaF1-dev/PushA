from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings


def build_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine.

    :param settings: Explicit settings or ``None`` to use the cached configuration.
    :returns: Configured asynchronous database engine.
    """
    current_settings = settings or get_settings()
    return create_async_engine(
        str(current_settings.database_url),
        echo=current_settings.postgres_sql_echo,
        pool_pre_ping=True,
    )


engine = build_engine()

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a session lifecycle without coupling the DB layer to FastAPI.

    :yields: Open asynchronous SQLAlchemy session.
    :raises Exception: Re-raises the original error after rolling back the session.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Release pooled database connections during application shutdown.

    :returns: ``None``.
    """
    await engine.dispose()
