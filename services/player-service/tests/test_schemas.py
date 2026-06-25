import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.domain import (
    Player,
    PlayerStatus,
    TeammateReview,
    ValorantProfile,
    ValorantRank,
    ValorantRole,
)
from app.schemas import (
    CreatePlayerRequest,
    CreateReviewRequest,
    PlayerDetailsResponse,
    PlayerResponse,
    ReviewPagination,
    ReviewResponse,
    UpdatePlayerStatusRequest,
    UpdateValorantProfileRequest,
    ValorantProfileResponse,
)


def make_profile(player_id=None) -> ValorantProfile:
    return ValorantProfile(
        player_id=player_id or uuid4(),
        region="EU",
        current_rank=ValorantRank.GOLD_2,
        main_roles=frozenset({ValorantRole.CONTROLLER, ValorantRole.SENTINEL}),
        status=PlayerStatus.READY_TO_PLAY,
    )


# noinspection PyTypeChecker
class PlayerSchemaTests(unittest.TestCase):
    def test_create_player_normalizes_strings_and_roles(self) -> None:
        request = CreatePlayerRequest(
            nickname="  Sage Main  ",
            riot_id="  Sage#EU  ",
            region=" eu ",
            current_rank="GOLD_2",
            main_roles=["SENTINEL", "SENTINEL"],
        )

        self.assertEqual(request.nickname, "Sage Main")
        self.assertEqual(request.riot_id, "Sage#EU")
        self.assertEqual(request.region, "EU")
        self.assertEqual(request.main_roles, frozenset({ValorantRole.SENTINEL}))

    def test_create_player_rejects_empty_roles(self) -> None:
        with self.assertRaises(ValidationError):
            CreatePlayerRequest(
                nickname="Sage",
                riot_id="Sage#EU",
                region="EU",
                current_rank="GOLD_2",
                main_roles=[],
            )

    def test_unknown_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            CreatePlayerRequest(
                nickname="Sage",
                riot_id="Sage#EU",
                region="EU",
                current_rank="GOLD_2",
                main_roles=["SENTINEL"],
                unknown="value",
            )

    def test_response_is_created_from_domain_entities(self) -> None:
        player = Player(nickname="Sage", riot_id="Sage#EU")
        profile = make_profile(player.id)

        response = PlayerDetailsResponse(
            player=PlayerResponse.model_validate(player),
            valorant_profile=ValorantProfileResponse.model_validate(profile),
        )
        payload = response.model_dump(mode="json")

        self.assertEqual(payload["player"]["id"], str(player.id))
        self.assertEqual(payload["valorant_profile"]["region"], "EU")
        self.assertCountEqual(
            payload["valorant_profile"]["main_roles"],
            ["CONTROLLER", "SENTINEL"],
        )


# noinspection PyTypeChecker
class ProfileSchemaTests(unittest.TestCase):
    def test_partial_update_requires_at_least_one_field(self) -> None:
        with self.assertRaises(ValidationError):
            UpdateValorantProfileRequest()

    def test_partial_update_normalizes_region(self) -> None:
        request = UpdateValorantProfileRequest(region=" na ")
        self.assertEqual(request.region, "NA")

    def test_status_request_parses_domain_enum(self) -> None:
        request = UpdatePlayerStatusRequest(status="READY_TO_PLAY")
        self.assertIs(request.status, PlayerStatus.READY_TO_PLAY)


class ReviewSchemaTests(unittest.TestCase):
    def test_create_review_normalizes_blank_comment(self) -> None:
        request = CreateReviewRequest(
            reviewer_id=uuid4(),
            rating=5,
            comment="   ",
        )
        self.assertIsNone(request.comment)

    def test_create_review_rejects_invalid_or_boolean_rating(self) -> None:
        for rating in (0, 6, True):
            with self.subTest(rating=rating), self.assertRaises(ValidationError):
                CreateReviewRequest(reviewer_id=uuid4(), rating=rating)

    def test_review_response_is_created_from_domain_entity(self) -> None:
        review = TeammateReview(uuid4(), uuid4(), 4, "Good")
        response = ReviewResponse.model_validate(review)
        self.assertEqual(response.id, review.id)
        self.assertEqual(response.rating, 4)

    def test_pagination_validates_bounds(self) -> None:
        self.assertEqual(ReviewPagination().limit, 100)
        with self.assertRaises(ValidationError):
            ReviewPagination(limit=101)


if __name__ == "__main__":
    unittest.main()
