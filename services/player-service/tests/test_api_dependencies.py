import unittest

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PlayerServiceDependency,
    ProfileServiceDependency,
    ReviewServiceDependency,
    get_db_session,
    get_player_repository,
    get_player_service,
    get_profile_repository,
    get_profile_service,
    get_review_repository,
    get_review_service,
    get_transaction_manager,
)
from app.db import AsyncSessionFactory, SqlAlchemyTransactionManager
from app.repositories.sqlalchemy import (
    SqlAlchemyPlayerRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyReviewRepository,
)
from app.services import PlayerService, ProfileService, ReviewService


class DependencyFactoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.session = AsyncSessionFactory()

    async def asyncTearDown(self) -> None:
        await self.session.close()

    async def test_session_dependency_yields_async_session(self) -> None:
        dependency = get_db_session()
        session = await anext(dependency)
        try:
            self.assertIsInstance(session, AsyncSession)
        finally:
            await dependency.aclose()

    async def test_infrastructure_dependencies_share_session(self) -> None:
        players = get_player_repository(self.session)
        profiles = get_profile_repository(self.session)
        reviews = get_review_repository(self.session)
        transaction = get_transaction_manager(self.session)

        self.assertIsInstance(players, SqlAlchemyPlayerRepository)
        self.assertIsInstance(profiles, SqlAlchemyProfileRepository)
        self.assertIsInstance(reviews, SqlAlchemyReviewRepository)
        self.assertIsInstance(transaction, SqlAlchemyTransactionManager)
        self.assertIs(players._session, self.session)
        self.assertIs(profiles._session, self.session)
        self.assertIs(reviews._session, self.session)
        self.assertIs(transaction._session, self.session)

    async def test_service_factories_compose_expected_services(self) -> None:
        players = get_player_repository(self.session)
        profiles = get_profile_repository(self.session)
        reviews = get_review_repository(self.session)
        transaction = get_transaction_manager(self.session)

        self.assertIsInstance(
            get_player_service(players, profiles, transaction), PlayerService
        )
        self.assertIsInstance(
            get_profile_service(profiles, transaction), ProfileService
        )
        self.assertIsInstance(
            get_review_service(players, profiles, reviews, transaction),
            ReviewService,
        )


class FastApiDependencyGraphTests(unittest.TestCase):
    def test_fastapi_accepts_all_service_dependency_aliases(self) -> None:
        app = FastAPI()

        @app.get("/dependency-probe")
        async def dependency_probe(
            player_service: PlayerServiceDependency,
            profile_service: ProfileServiceDependency,
            review_service: ReviewServiceDependency,
        ) -> dict[str, bool]:
            return {
                "player": isinstance(player_service, PlayerService),
                "profile": isinstance(profile_service, ProfileService),
                "review": isinstance(review_service, ReviewService),
            }

        route_paths = {route.path for route in app.routes}
        self.assertIn("/dependency-probe", route_paths)


if __name__ == "__main__":
    unittest.main()
