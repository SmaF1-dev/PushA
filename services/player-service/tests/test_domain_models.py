import unittest
from uuid import uuid4

from ..app.domain import (
    InvalidPlayerError,
    InvalidProfileError,
    InvalidReviewError,
    Player,
    PlayerStatus,
    TeammateReview,
    ValorantProfile,
    ValorantRank,
    ValorantRole,
)


def make_profile() -> ValorantProfile:
    return ValorantProfile(
        player_id=uuid4(),
        region="eu",
        current_rank=ValorantRank.GOLD_2,
        main_roles=frozenset({ValorantRole.CONTROLLER}),
    )


class PlayerTests(unittest.TestCase):
    def test_normalizes_required_text(self) -> None:
        player = Player(nickname="  Sage Main  ", riot_id="  Player#EUW  ")

        self.assertEqual(player.nickname, "Sage Main")
        self.assertEqual(player.riot_id, "Player#EUW")

    def test_rejects_empty_nickname(self) -> None:
        with self.assertRaises(InvalidPlayerError):
            Player(nickname="   ", riot_id="Player#EUW")


class ProfileTests(unittest.TestCase):
    def test_normalizes_region_and_removes_duplicate_roles(self) -> None:
        profile = ValorantProfile(
            player_id=uuid4(),
            region=" eu ",
            current_rank=ValorantRank.GOLD_2,
            main_roles=frozenset({ValorantRole.CONTROLLER, ValorantRole.CONTROLLER}),
        )

        self.assertEqual(profile.region, "EU")
        self.assertEqual(profile.main_roles, frozenset({ValorantRole.CONTROLLER}))
        self.assertIs(profile.status, PlayerStatus.OFFLINE)

    def test_requires_at_least_one_role(self) -> None:
        with self.assertRaises(InvalidProfileError):
            ValorantProfile(
                player_id=uuid4(),
                region="EU",
                current_rank=ValorantRank.GOLD_2,
                main_roles=frozenset(),
            )

    def test_updates_game_details_and_status(self) -> None:
        profile = make_profile()

        profile.update_game_details(
            region="na",
            current_rank=ValorantRank.PLATINUM_1,
            main_roles={ValorantRole.INITIATOR, ValorantRole.SENTINEL},
        )
        profile.change_status(PlayerStatus.READY_TO_PLAY)

        self.assertEqual(profile.region, "NA")
        self.assertIs(profile.current_rank, ValorantRank.PLATINUM_1)
        self.assertEqual(
            profile.main_roles,
            frozenset({ValorantRole.INITIATOR, ValorantRole.SENTINEL}),
        )
        self.assertIs(profile.status, PlayerStatus.READY_TO_PLAY)

    def test_recalculates_rating_from_reviews(self) -> None:
        profile = make_profile()

        profile.recalculate_rating([5, 4, 3])

        self.assertEqual(profile.teammate_rating, 4.0)
        self.assertEqual(profile.reviews_count, 3)


class ReviewTests(unittest.TestCase):
    def test_rejects_self_review(self) -> None:
        player_id = uuid4()

        with self.assertRaises(InvalidReviewError):
            TeammateReview(
                reviewer_id=player_id,
                target_player_id=player_id,
                rating=5,
            )

    def test_rejects_invalid_rating(self) -> None:
        for rating in (0, 6, 4.5, True):
            with self.subTest(rating=rating), self.assertRaises(InvalidReviewError):
                TeammateReview(
                    reviewer_id=uuid4(),
                    target_player_id=uuid4(),
                    rating=rating,  # type: ignore[arg-type]
                )


class RankTests(unittest.TestCase):
    def test_checks_inclusive_range(self) -> None:
        self.assertTrue(
            ValorantRank.GOLD_2.is_between_or_equal(
                ValorantRank.GOLD_1, ValorantRank.PLATINUM_3
            )
        )
        self.assertFalse(
            ValorantRank.SILVER_3.is_between_or_equal(
                ValorantRank.GOLD_1, ValorantRank.PLATINUM_3
            )
        )

    def test_rejects_inverted_range(self) -> None:
        with self.assertRaises(ValueError):
            ValorantRank.GOLD_1.is_between_or_equal(
                ValorantRank.PLATINUM_1, ValorantRank.GOLD_1
            )


if __name__ == "__main__":
    unittest.main()
