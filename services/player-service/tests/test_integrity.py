import unittest

from sqlalchemy.exc import IntegrityError

from app.db.integrity import RIOT_ID_UNIQUE_CONSTRAINT, find_constraint_name
from app.domain import Player
from app.repositories.exceptions import DuplicateRiotIdError
from app.repositories.sqlalchemy import SqlAlchemyPlayerRepository


class DriverUniqueViolation(Exception):
    """Represent the constraint metadata exposed by ``asyncpg``."""

    constraint_name = RIOT_ID_UNIQUE_CONSTRAINT


class FailingSession:
    """Provide the small session surface needed by the player repository."""

    def __init__(self, error: IntegrityError) -> None:
        """Store the integrity failure emitted by ``flush``.

        :param error: SQLAlchemy error to raise.
        """
        self.error = error
        self.added = None

    def add(self, model) -> None:
        """Record an ORM model scheduled for insertion.

        :param model: SQLAlchemy player model.
        :returns: ``None``.
        """
        self.added = model

    async def flush(self) -> None:
        """Simulate the database rejecting a duplicate Riot ID.

        :raises IntegrityError: Always, to imitate PostgreSQL.
        """
        raise self.error


class IntegrityHandlingTests(unittest.IsolatedAsyncioTestCase):
    """Verify translation of PostgreSQL uniqueness violations."""

    async def test_repository_translates_riot_id_constraint(self) -> None:
        """Convert the named DB constraint into a repository error."""
        integrity_error = IntegrityError(
            "INSERT INTO players ...",
            {},
            DriverUniqueViolation(),
        )
        session = FailingSession(integrity_error)
        repository = SqlAlchemyPlayerRepository(session)

        with self.assertRaises(DuplicateRiotIdError):
            await repository.add(Player(nickname="Race", riot_id="Race#EU"))

        self.assertEqual(find_constraint_name(integrity_error), RIOT_ID_UNIQUE_CONSTRAINT)


if __name__ == "__main__":
    unittest.main()
