from sqlalchemy.ext.asyncio import AsyncSession

from app.services.transactions import TransactionManager


class SqlAlchemyTransactionManager(TransactionManager):
    """Manage transactions through an injected SQLAlchemy session.

    :param session: Session whose transaction is controlled by this adapter.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """Commit pending changes.

        :returns: ``None``.
        :raises sqlalchemy.exc.SQLAlchemyError: If the commit fails.
        """
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back pending changes.

        :returns: ``None``.
        :raises sqlalchemy.exc.SQLAlchemyError: If the rollback fails.
        """
        await self._session.rollback()
