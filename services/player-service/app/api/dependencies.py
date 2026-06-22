from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import session_scope


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Inject one database session into an HTTP request."""
    async with session_scope() as session:
        yield session


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
