from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_scope
from app.db.transaction import SqlAlchemyTransactionManager
from app.repositories.interfaces import (
    PlayerRepository,
    ProfileRepository,
    ReviewRepository,
)
from app.repositories.sqlalchemy import (
    SqlAlchemyPlayerRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyReviewRepository,
)
from app.services import PlayerService, ProfileService, ReviewService
from app.services.transactions import TransactionManager


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Inject one database session into an HTTP request.

    FastAPI caches this dependency within a request, so every repository and
    transaction adapter receives the same session instance.

    :yields: Session scoped to the current request.
    :raises Exception: Re-raises an application error after rolling back the session.
    """
    async with session_scope() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_player_repository(session: DatabaseSession) -> PlayerRepository:
    """Create the request-scoped player repository.

    :param session: Database session injected for the current request.
    :returns: SQLAlchemy player repository using that session.
    """
    return SqlAlchemyPlayerRepository(session)


PlayerRepositoryDependency = Annotated[
    PlayerRepository,
    Depends(get_player_repository),
]


def get_profile_repository(session: DatabaseSession) -> ProfileRepository:
    """Create the request-scoped Valorant profile repository.

    :param session: Database session injected for the current request.
    :returns: SQLAlchemy profile repository using that session.
    """
    return SqlAlchemyProfileRepository(session)


ProfileRepositoryDependency = Annotated[
    ProfileRepository,
    Depends(get_profile_repository),
]


def get_review_repository(session: DatabaseSession) -> ReviewRepository:
    """Create the request-scoped teammate review repository.

    :param session: Database session injected for the current request.
    :returns: SQLAlchemy review repository using that session.
    """
    return SqlAlchemyReviewRepository(session)


ReviewRepositoryDependency = Annotated[
    ReviewRepository,
    Depends(get_review_repository),
]


def get_transaction_manager(session: DatabaseSession) -> TransactionManager:
    """Create the request-scoped transaction adapter.

    :param session: Database session shared by all request repositories.
    :returns: SQLAlchemy transaction manager using that session.
    """
    return SqlAlchemyTransactionManager(session)


TransactionManagerDependency = Annotated[
    TransactionManager,
    Depends(get_transaction_manager),
]


def get_player_service(
    players: PlayerRepositoryDependency,
    profiles: ProfileRepositoryDependency,
    transaction: TransactionManagerDependency,
) -> PlayerService:
    """Compose the player application service.

    :param players: Request-scoped player repository.
    :param profiles: Request-scoped profile repository.
    :param transaction: Request-scoped transaction boundary.
    :returns: Fully configured player service.
    """
    return PlayerService(players, profiles, transaction)


PlayerServiceDependency = Annotated[
    PlayerService,
    Depends(get_player_service),
]


def get_profile_service(
    profiles: ProfileRepositoryDependency,
    transaction: TransactionManagerDependency,
) -> ProfileService:
    """Compose the Valorant profile application service.

    :param profiles: Request-scoped profile repository.
    :param transaction: Request-scoped transaction boundary.
    :returns: Fully configured profile service.
    """
    return ProfileService(profiles, transaction)


ProfileServiceDependency = Annotated[
    ProfileService,
    Depends(get_profile_service),
]


def get_review_service(
    players: PlayerRepositoryDependency,
    profiles: ProfileRepositoryDependency,
    reviews: ReviewRepositoryDependency,
    transaction: TransactionManagerDependency,
) -> ReviewService:
    """Compose the teammate review application service.

    :param players: Request-scoped player repository.
    :param profiles: Request-scoped profile repository.
    :param reviews: Request-scoped review repository.
    :param transaction: Request-scoped transaction boundary.
    :returns: Fully configured review service.
    """
    return ReviewService(players, profiles, reviews, transaction)


ReviewServiceDependency = Annotated[
    ReviewService,
    Depends(get_review_service),
]


__all__ = [
    "DatabaseSession",
    "PlayerRepositoryDependency",
    "PlayerServiceDependency",
    "ProfileRepositoryDependency",
    "ProfileServiceDependency",
    "ReviewRepositoryDependency",
    "ReviewServiceDependency",
    "TransactionManagerDependency",
    "get_db_session",
    "get_player_repository",
    "get_player_service",
    "get_profile_repository",
    "get_profile_service",
    "get_review_repository",
    "get_review_service",
    "get_transaction_manager",
]
