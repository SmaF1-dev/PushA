import unittest

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db import AsyncSessionFactory, Base, engine
from app.db.models import PlayerModel, TeammateReviewModel, ValorantProfileModel


class DatabaseMetadataTests(unittest.TestCase):
    def test_player_service_owns_expected_tables(self) -> None:
        self.assertEqual(
            set(Base.metadata.tables),
            {"players", "valorant_profiles", "teammate_reviews"},
        )

    def test_models_are_registered_in_metadata(self) -> None:
        self.assertIs(PlayerModel.__table__, Base.metadata.tables["players"])
        self.assertIs(
            ValorantProfileModel.__table__, Base.metadata.tables["valorant_profiles"]
        )
        self.assertIs(
            TeammateReviewModel.__table__, Base.metadata.tables["teammate_reviews"]
        )

    def test_async_engine_uses_asyncpg(self) -> None:
        self.assertIsInstance(engine, AsyncEngine)
        self.assertEqual(engine.url.drivername, "postgresql+asyncpg")

    def test_session_factory_creates_async_sessions(self) -> None:
        session = AsyncSessionFactory()
        try:
            self.assertIsInstance(session, AsyncSession)
            self.assertFalse(session.sync_session.expire_on_commit)
        finally:
            # No connection is acquired until the session executes a query.
            import asyncio

            asyncio.run(session.close())


if __name__ == "__main__":
    unittest.main()
