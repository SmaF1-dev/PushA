from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from app.db.session import session_scope
from app.repositories.sqlalchemy import SqlAlchemyPlayerQueryRepository
from app.services import PlayerQueryService


PlayerQueryServiceScope = Callable[
    [],
    AbstractAsyncContextManager[PlayerQueryService],
]


@asynccontextmanager
async def player_query_service_scope() -> AsyncIterator[PlayerQueryService]:
    """Compose a query service for one gRPC request.

    Each invocation receives an independent SQLAlchemy session. This mirrors
    FastAPI's request-scoped dependency graph without coupling gRPC to FastAPI.

    :yields: Player query service scoped to one RPC.
    :raises Exception: Re-raises application or persistence failures after rollback.
    """
    async with session_scope() as session:
        yield PlayerQueryService(SqlAlchemyPlayerQueryRepository(session))
