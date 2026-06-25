import argparse
import asyncio
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import delete

from app.db import AsyncSessionFactory, dispose_engine
from app.db.models import PlayerModel, TeammateReviewModel, ValorantProfileModel
from app.domain import PlayerStatus, ValorantRank, ValorantRole


SEED_NAMESPACE = UUID("897bdd9a-0655-4cd0-babb-5cb8ab74f092")
RIOT_ID_PREFIX = "grpc-test-"
DEFAULT_PLAYER_COUNT = 48
MINIMUM_PLAYER_COUNT = 12

REGIONS = ("EU", "NA", "AP", "LATAM")
STATUSES = tuple(PlayerStatus)
RANKS = tuple(ValorantRank)
ROLE_SETS = (
    (ValorantRole.CONTROLLER,),
    (ValorantRole.SENTINEL,),
    (ValorantRole.INITIATOR,),
    (ValorantRole.DUELIST,),
    (ValorantRole.CONTROLLER, ValorantRole.SENTINEL),
    (ValorantRole.INITIATOR, ValorantRole.DUELIST),
)
SEARCH_POOL_RANKS = (
    ValorantRank.GOLD_1,
    ValorantRank.GOLD_2,
    ValorantRank.GOLD_3,
    ValorantRank.PLATINUM_1,
    ValorantRank.PLATINUM_2,
    ValorantRank.PLATINUM_3,
)
HIGH_RATING_PATTERNS = (
    (5, 5, 5),
    (5, 5, 4),
    (5, 4, 4),
    (4, 4, 4),
)


@dataclass(frozen=True, slots=True)
class SeedProfile:
    """Describe one deterministic player and their generated reviews.

    :param index: Stable zero-based seed index.
    :param player_id: Deterministic player UUID.
    :param profile_id: Deterministic profile UUID.
    :param region: Matchmaking region.
    :param rank: Current Valorant rank.
    :param roles: Preferred roles.
    :param status: Current availability status.
    :param ratings: Ratings received from other seeded players.
    """

    index: int
    player_id: UUID
    profile_id: UUID
    region: str
    rank: ValorantRank
    roles: tuple[ValorantRole, ...]
    status: PlayerStatus
    ratings: tuple[int, ...]

    @property
    def teammate_rating(self) -> Decimal:
        """Calculate the persisted aggregate rating.

        :returns: Two-decimal average or zero when there are no reviews.
        """
        if not self.ratings:
            return Decimal("0.00")
        average = Decimal(sum(self.ratings)) / Decimal(len(self.ratings))
        return average.quantize(Decimal("0.01"))


def seeded_uuid(kind: str, index: int) -> UUID:
    """Create a stable UUID for a seeded object.

    :param kind: Object category included in the UUID name.
    :param index: Stable object index.
    :returns: Deterministic UUIDv5.
    """
    return uuid5(SEED_NAMESPACE, f"{kind}-{index}")


def build_seed_profiles(count: int) -> list[SeedProfile]:
    """Build diverse profiles with a guaranteed matchmaking search pool.

    The first third is deliberately eligible for the default client filters:
    EU, Gold–Platinum, READY_TO_PLAY, and rating of at least four. Remaining
    profiles cover every region, status, rank, role, and low-rating scenario.

    :param count: Number of players to generate.
    :returns: Deterministic profile specifications.
    :raises ValueError: If fewer than twelve players are requested.
    """
    if count < MINIMUM_PLAYER_COUNT:
        raise ValueError(f"count must be at least {MINIMUM_PLAYER_COUNT}")

    search_pool_size = max(12, count // 3)
    profiles: list[SeedProfile] = []
    for index in range(count):
        if index < search_pool_size:
            region = "EU"
            rank = SEARCH_POOL_RANKS[index % len(SEARCH_POOL_RANKS)]
            roles = ROLE_SETS[index % len(ROLE_SETS)]
            status = PlayerStatus.READY_TO_PLAY
            ratings = HIGH_RATING_PATTERNS[index % len(HIGH_RATING_PATTERNS)]
        else:
            region = REGIONS[index % len(REGIONS)]
            rank = RANKS[index % len(RANKS)]
            roles = ROLE_SETS[index % len(ROLE_SETS)]
            status = STATUSES[index % len(STATUSES)]
            ratings = (
                ()
                if index % 7 == 0
                else tuple(
                    1 + ((index + review_index) % 5)
                    for review_index in range(1 + index % 5)
                )
            )

        profiles.append(
            SeedProfile(
                index=index,
                player_id=seeded_uuid("player", index),
                profile_id=seeded_uuid("profile", index),
                region=region,
                rank=rank,
                roles=roles,
                status=status,
                ratings=ratings,
            )
        )
    return profiles


async def replace_seed_data(count: int) -> list[SeedProfile]:
    """Replace only gRPC seed records in one database transaction.

    :param count: Number of players to create.
    :returns: Generated profile specifications.
    :raises sqlalchemy.exc.SQLAlchemyError: If PostgreSQL rejects the operation.
    """
    profiles = build_seed_profiles(count)
    async with AsyncSessionFactory.begin() as session:
        await session.execute(
            delete(PlayerModel).where(
                PlayerModel.riot_id.like(f"{RIOT_ID_PREFIX}%")
            )
        )

        session.add_all(
            [
                PlayerModel(
                    id=profile.player_id,
                    nickname=f"GrpcTestPlayer{profile.index:03d}",
                    riot_id=f"{RIOT_ID_PREFIX}{profile.index:03d}#SEED",
                )
                for profile in profiles
            ]
        )
        await session.flush()

        session.add_all(
            [
                ValorantProfileModel(
                    id=profile.profile_id,
                    player_id=profile.player_id,
                    region=profile.region,
                    current_rank=profile.rank,
                    main_roles=list(profile.roles),
                    status=profile.status,
                    teammate_rating=profile.teammate_rating,
                    reviews_count=len(profile.ratings),
                )
                for profile in profiles
            ]
        )

        reviews: list[TeammateReviewModel] = []
        for target in profiles:
            for review_index, rating in enumerate(target.ratings):
                reviewer = profiles[(target.index + review_index + 1) % count]
                reviews.append(
                    TeammateReviewModel(
                        id=uuid5(
                            SEED_NAMESPACE,
                            f"review-{target.index}-{review_index}",
                        ),
                        reviewer_id=reviewer.player_id,
                        target_player_id=target.player_id,
                        rating=rating,
                        comment=(
                            f"Generated gRPC test review {review_index + 1}"
                        ),
                    )
                )
        session.add_all(reviews)

    return profiles


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options.

    :returns: Parsed player count.
    """
    parser = argparse.ArgumentParser(
        description="Replace deterministic gRPC test data in Player Service",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_PLAYER_COUNT,
        help=f"number of players to create (minimum {MINIMUM_PLAYER_COUNT})",
    )
    return parser.parse_args()


async def async_main(count: int) -> None:
    """Populate the database and print useful client parameters.

    :param count: Number of players to create.
    :returns: ``None``.
    """
    try:
        profiles = await replace_seed_data(count)
        review_count = sum(len(profile.ratings) for profile in profiles)
        default_player = profiles[0]
        print(f"Created {len(profiles)} players and profiles")
        print(f"Created {review_count} teammate reviews")
        print(f"Default gRPC player_id: {default_player.player_id}")
        print(
            "Default search: region=EU, ranks=GOLD_1..PLATINUM_3, "
            "status=READY_TO_PLAY, min_rating=4.0"
        )
    finally:
        await dispose_engine()


def main() -> None:
    """Run the asynchronous seed command and dispose the shared DB engine.

    :returns: ``None``.
    """
    arguments = parse_arguments()
    asyncio.run(async_main(arguments.count))


if __name__ == "__main__":
    main()
