import unittest
from uuid import uuid4

from app.domain import (
    Player,
    PlayerStatus,
    TeammateReview,
    ValorantProfile,
    ValorantRank,
    ValorantRole,
)
from app.repositories import (
    PlayerRepository,
    ProfileRepository,
    ReviewRepository,
    SqlAlchemyPlayerRepository,
    SqlAlchemyProfileRepository,
    SqlAlchemyReviewRepository,
)
from app.repositories.mappers import (
    player_to_domain,
    player_to_model,
    profile_to_domain,
    profile_to_model,
    review_to_domain,
    review_to_model,
)
from tests.fakes import (
    FakePlayerRepository,
    FakeProfileRepository,
    FakeReviewRepository,
)


def make_profile(player_id=None) -> ValorantProfile:
    return ValorantProfile(
        player_id=player_id or uuid4(),
        region="EU",
        current_rank=ValorantRank.GOLD_2,
        main_roles=frozenset({ValorantRole.CONTROLLER, ValorantRole.SENTINEL}),
        status=PlayerStatus.READY_TO_PLAY,
    )


class RepositoryInterfaceTests(unittest.TestCase):
    def test_sqlalchemy_repositories_implement_interfaces(self) -> None:
        self.assertTrue(issubclass(SqlAlchemyPlayerRepository, PlayerRepository))
        self.assertTrue(issubclass(SqlAlchemyProfileRepository, ProfileRepository))
        self.assertTrue(issubclass(SqlAlchemyReviewRepository, ReviewRepository))

    def test_fake_repositories_implement_interfaces(self) -> None:
        self.assertTrue(issubclass(FakePlayerRepository, PlayerRepository))
        self.assertTrue(issubclass(FakeProfileRepository, ProfileRepository))
        self.assertTrue(issubclass(FakeReviewRepository, ReviewRepository))


class RepositoryMapperTests(unittest.TestCase):
    def test_player_round_trip(self) -> None:
        player = Player(nickname="Sage Main", riot_id="Sage#EU")
        self.assertEqual(player_to_domain(player_to_model(player)), player)

    def test_profile_round_trip(self) -> None:
        profile = make_profile()
        self.assertEqual(profile_to_domain(profile_to_model(profile)), profile)

    def test_review_round_trip(self) -> None:
        review = TeammateReview(
            reviewer_id=uuid4(),
            target_player_id=uuid4(),
            rating=5,
            comment="Great teammate",
        )
        self.assertEqual(review_to_domain(review_to_model(review)), review)


class FakePlayerRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_add_and_find_player(self) -> None:
        repository = FakePlayerRepository()
        player = Player(nickname="Omen Main", riot_id="Omen#EU")

        await repository.add(player)

        self.assertEqual(await repository.get_by_id(player.id), player)
        self.assertEqual(await repository.get_by_riot_id(player.riot_id), player)
        self.assertTrue(await repository.exists_by_riot_id(player.riot_id))

    async def test_returns_copies_not_shared_domain_objects(self) -> None:
        player = Player(nickname="Omen Main", riot_id="Omen#EU")
        repository = FakePlayerRepository([player])

        loaded = await repository.get_by_id(player.id)
        assert loaded is not None
        loaded.rename("Changed")

        stored = await repository.get_by_id(player.id)
        assert stored is not None
        self.assertEqual(stored.nickname, "Omen Main")


class FakeProfileRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_add_get_and_update_profile(self) -> None:
        profile = make_profile()
        repository = FakeProfileRepository()
        await repository.add(profile)

        profile.change_status(PlayerStatus.IN_GAME)
        updated = await repository.update(profile)

        self.assertIsNotNone(updated)
        stored = await repository.get_by_player_id(profile.player_id)
        assert stored is not None
        self.assertIs(stored.status, PlayerStatus.IN_GAME)


class FakeReviewRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_lists_reviews_and_ratings_for_target(self) -> None:
        target_id = uuid4()
        first = TeammateReview(uuid4(), target_id, 4, "Good")
        second = TeammateReview(uuid4(), target_id, 5, "Great")
        other = TeammateReview(uuid4(), uuid4(), 1, "Other player")
        repository = FakeReviewRepository([first, second, other])

        reviews = await repository.list_for_target(target_id)
        ratings = await repository.list_ratings_for_target(target_id)

        self.assertEqual({review.id for review in reviews}, {first.id, second.id})
        self.assertCountEqual(ratings, [4, 5])


if __name__ == "__main__":
    unittest.main()
