import unittest
from uuid import uuid4

from app.domain import (
    InvalidReviewError,
    Player,
    PlayerStatus,
    ValorantProfile,
    ValorantRank,
    ValorantRole,
)
from app.services import (
    PlayerNotFoundError,
    PlayerService,
    ProfileNotFoundError,
    ProfileService,
    ReviewService,
    RiotIdAlreadyExistsError,
)
from tests.fakes import (
    FakePlayerRepository,
    FakeProfileRepository,
    FakeReviewRepository,
    FakeTransactionManager,
)


def make_profile(player_id) -> ValorantProfile:
    return ValorantProfile(
        player_id=player_id,
        region="EU",
        current_rank=ValorantRank.GOLD_2,
        main_roles=frozenset({ValorantRole.CONTROLLER}),
    )


class PlayerServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_player_and_profile_in_one_use_case(self) -> None:
        players = FakePlayerRepository()
        profiles = FakeProfileRepository()
        transaction = FakeTransactionManager()
        service = PlayerService(players, profiles, transaction)

        player, profile = await service.create_player(
            nickname="Sage Main",
            riot_id="Sage#EU",
            region="eu",
            current_rank=ValorantRank.PLATINUM_1,
            main_roles=[ValorantRole.SENTINEL],
        )

        self.assertEqual(profile.player_id, player.id)
        self.assertEqual(profile.region, "EU")
        self.assertEqual(await players.get_by_id(player.id), player)
        self.assertEqual(await profiles.get_by_player_id(player.id), profile)
        self.assertEqual(transaction.commits, 1)
        self.assertEqual(transaction.rollbacks, 0)

    async def test_rejects_duplicate_riot_id(self) -> None:
        existing = Player(nickname="Existing", riot_id="Same#EU")
        transaction = FakeTransactionManager()
        service = PlayerService(
            FakePlayerRepository([existing]),
            FakeProfileRepository(),
            transaction,
        )

        with self.assertRaises(RiotIdAlreadyExistsError):
            await service.create_player(
                nickname="New",
                riot_id="Same#EU",
                region="EU",
                current_rank=ValorantRank.GOLD_1,
                main_roles=[ValorantRole.DUELIST],
            )

        self.assertEqual(transaction.commits, 0)
        self.assertEqual(transaction.rollbacks, 1)

    async def test_get_missing_player_raises_expected_error(self) -> None:
        service = PlayerService(
            FakePlayerRepository(),
            FakeProfileRepository(),
            FakeTransactionManager(),
        )

        with self.assertRaises(PlayerNotFoundError):
            await service.get_player(uuid4())


class ProfileServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_updates_profile_status(self) -> None:
        profile = make_profile(uuid4())
        profiles = FakeProfileRepository([profile])
        transaction = FakeTransactionManager()
        service = ProfileService(profiles, transaction)

        updated = await service.update_status(profile.player_id, PlayerStatus.IN_GAME)

        self.assertIs(updated.status, PlayerStatus.IN_GAME)
        self.assertEqual(transaction.commits, 1)

    async def test_missing_profile_rolls_back(self) -> None:
        transaction = FakeTransactionManager()
        service = ProfileService(FakeProfileRepository(), transaction)

        with self.assertRaises(ProfileNotFoundError):
            await service.update_status(uuid4(), PlayerStatus.ONLINE)

        self.assertEqual(transaction.commits, 0)
        self.assertEqual(transaction.rollbacks, 1)


class ReviewServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_review_and_recalculates_rating(self) -> None:
        reviewer = Player(nickname="Reviewer", riot_id="Reviewer#EU")
        target = Player(nickname="Target", riot_id="Target#EU")
        profile = make_profile(target.id)
        profiles = FakeProfileRepository([profile])
        reviews = FakeReviewRepository()
        transaction = FakeTransactionManager()
        service = ReviewService(
            FakePlayerRepository([reviewer, target]),
            profiles,
            reviews,
            transaction,
        )

        review = await service.create_review(
            reviewer_id=reviewer.id,
            target_player_id=target.id,
            rating=5,
            comment="  Great teammate  ",
        )

        updated_profile = await profiles.get_by_player_id(target.id)
        assert updated_profile is not None
        self.assertEqual(review.comment, "Great teammate")
        self.assertEqual(updated_profile.teammate_rating, 5.0)
        self.assertEqual(updated_profile.reviews_count, 1)
        self.assertEqual(transaction.commits, 1)
        self.assertEqual(transaction.rollbacks, 0)

    async def test_self_review_is_rejected_and_rolled_back(self) -> None:
        player = Player(nickname="Solo", riot_id="Solo#EU")
        transaction = FakeTransactionManager()
        service = ReviewService(
            FakePlayerRepository([player]),
            FakeProfileRepository([make_profile(player.id)]),
            FakeReviewRepository(),
            transaction,
        )

        with self.assertRaises(InvalidReviewError):
            await service.create_review(
                reviewer_id=player.id,
                target_player_id=player.id,
                rating=5,
            )

        self.assertEqual(transaction.commits, 0)
        self.assertEqual(transaction.rollbacks, 1)

    async def test_missing_target_player_is_rejected(self) -> None:
        reviewer = Player(nickname="Reviewer", riot_id="Reviewer#EU")
        transaction = FakeTransactionManager()
        service = ReviewService(
            FakePlayerRepository([reviewer]),
            FakeProfileRepository(),
            FakeReviewRepository(),
            transaction,
        )

        with self.assertRaises(PlayerNotFoundError):
            await service.create_review(
                reviewer_id=reviewer.id,
                target_player_id=uuid4(),
                rating=4,
            )

        self.assertEqual(transaction.rollbacks, 1)


if __name__ == "__main__":
    unittest.main()
