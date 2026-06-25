from abc import ABC, abstractmethod


class TransactionManager(ABC):
    """Define the transaction operations required by write services."""

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction.

        :returns: ``None``.
        """

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction.

        :returns: ``None``.
        """
