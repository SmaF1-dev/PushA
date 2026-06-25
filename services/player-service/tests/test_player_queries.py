import unittest
from uuid import uuid4

from app.domain import (
    EligibilityReason,
    InvalidPlayerQueryError,
    PlayerProfileSnapshot,
    PlayerSelectionCriteria,
    PlayerStatus,
    ValorantRank,
    ValorantRole,
)
from app.services import PlayerQueryService
from tests.fakes import FakePlayerQueryRepository


def make_snapshot(
        *,
        region: str = "EU",
        rank: ValorantRank = ValorantRank.GOLD_2,
        status: PlayerStatus = PlayerStatus.READY_TO_PLAY,
        rating: float = 4.5,
        roles: frozenset[ValorantRole] = frozenset({ValorantRole.CONTROLLER}),
) -> PlayerProfileSnapshot:
    """Build a player/profile projection for query tests.

    :param region: Matchmaking region.
    :param rank: Current Valorant rank.
    :param status: Current availability status.
    :param rating: Aggregate teammate rating.
    :param roles: Preferred Valorant roles.
    :returns: Test player projection.
    """
    player_id = uuid4()
    return PlayerProfileSnapshot(
        player_id=player_id,
        nickname=f"Player-{player_id}",
        riot_id=f"Player-{player_id}#EU",
        region=region,
        current_rank=rank,
        main_roles=roles,
        status=status,
        teammate_rating=rating,
        reviews_count=10,
    )


def make_criteria(**overrides) -> PlayerSelectionCriteria:
    """Build standard selection criteria with optional overrides.

    :param overrides: Field values replacing test defaults.
    :returns: Validated selection criteria.
    """
    values = {
        "min_rank": ValorantRank.GOLD_1,
        "max_rank": ValorantRank.PLATINUM_3,
        "required_status": PlayerStatus.READY_TO_PLAY,
        "min_teammate_rating": 4.0,
        "region": "eu",
        "required_roles": frozenset({ValorantRole.CONTROLLER}),
        "limit": 10,
    }
    values.update(overrides)
    return PlayerSelectionCriteria(**values)


class PlayerSelectionCriteriaTests(unittest.TestCase):
    """Verify matchmaking criteria invariants and reason codes."""

    def test_normalizes_region_and_builds_inclusive_rank_range(self) -> None:
        """Normalize region and expose every accepted rank."""
        criteria = make_criteria()

        self.assertEqual(criteria.region, "EU")
        self.assertIn(ValorantRank.GOLD_1, criteria.accepted_ranks)
        self.assertIn(ValorantRank.PLATINUM_3, criteria.accepted_ranks)
        self.assertNotIn(ValorantRank.SILVER_3, criteria.accepted_ranks)

    def test_reports_every_failed_eligibility_rule(self) -> None:
        """Return stable reasons for all mismatched player attributes."""
        profile = make_snapshot(
            region="NA",
            rank=ValorantRank.SILVER_1,
            status=PlayerStatus.OFFLINE,
            rating=2.0,
            roles=frozenset({ValorantRole.DUELIST}),
        )

        reasons = make_criteria().rejection_reasons(profile)

        self.assertEqual(
            reasons,
            (
                EligibilityReason.RANK_OUT_OF_RANGE,
                EligibilityReason.STATUS_MISMATCH,
                EligibilityReason.RATING_BELOW_MINIMUM,
                EligibilityReason.REGION_MISMATCH,
                EligibilityReason.ROLE_MISMATCH,
            ),
        )

    def test_rejects_inverted_rank_range_and_invalid_limit(self) -> None:
        """Reject criteria that cannot represent a valid query."""
        with self.assertRaises(InvalidPlayerQueryError):
            make_criteria(
                min_rank=ValorantRank.DIAMOND_1,
                max_rank=ValorantRank.GOLD_1,
            )
        with self.assertRaises(InvalidPlayerQueryError):
            make_criteria(limit=0)


class PlayerQueryServiceTests(unittest.IsolatedAsyncioTestCase):
    """Verify query orchestration against a fake repository."""

    async def test_finds_only_matching_non_excluded_players(self) -> None:
        """Delegate filtering while preserving domain criteria semantics."""
        excluded = make_snapshot(rating=5.0)
        matching = make_snapshot(rating=4.7)
        wrong_region = make_snapshot(region="NA", rating=4.9)
        service = PlayerQueryService(
            FakePlayerQueryRepository([excluded, matching, wrong_region])
        )

        profiles = await service.find_players(
            make_criteria(excluded_player_id=excluded.player_id)
        )

        self.assertEqual(list(profiles), [matching])

    async def test_returns_not_found_eligibility_reason(self) -> None:
        """Represent a missing player without transport-specific exceptions."""
        service = PlayerQueryService(FakePlayerQueryRepository())

        result = await service.check_eligibility(uuid4(), make_criteria())

        self.assertFalse(result.eligible)
        self.assertEqual(result.reasons, (EligibilityReason.PLAYER_NOT_FOUND,))


if __name__ == "__main__":
    unittest.main()
