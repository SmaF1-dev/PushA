"""create_player_schema

Revision ID: 260622_001
Revises:
Create Date: 2026-06-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "260622_001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


RANKS = (
    "IRON_1", "IRON_2", "IRON_3",
    "BRONZE_1", "BRONZE_2", "BRONZE_3",
    "SILVER_1", "SILVER_2", "SILVER_3",
    "GOLD_1", "GOLD_2", "GOLD_3",
    "PLATINUM_1", "PLATINUM_2", "PLATINUM_3",
    "DIAMOND_1", "DIAMOND_2", "DIAMOND_3",
    "ASCENDANT_1", "ASCENDANT_2", "ASCENDANT_3",
    "IMMORTAL_1", "IMMORTAL_2", "IMMORTAL_3",
    "RADIANT",
)
ROLES = ("DUELIST", "CONTROLLER", "INITIATOR", "SENTINEL")
STATUSES = ("OFFLINE", "ONLINE", "READY_TO_PLAY", "IN_GAME", "BUSY")


def upgrade() -> None:
    bind = op.get_bind()

    rank_enum = postgresql.ENUM(*RANKS, name="valorant_rank")
    role_enum = postgresql.ENUM(*ROLES, name="valorant_role")
    status_enum = postgresql.ENUM(*STATUSES, name="player_status")
    rank_enum.create(bind, checkfirst=True)
    role_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "players",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nickname", sa.String(length=100), nullable=False),
        sa.Column("riot_id", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "length(btrim(nickname)) > 0", name="nickname_not_blank"
        ),
        sa.CheckConstraint(
            "length(btrim(riot_id)) > 0", name="riot_id_not_blank"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_players"),
        sa.UniqueConstraint("riot_id", name="uq_players_riot_id"),
    )

    op.create_table(
        "valorant_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("region", sa.String(length=32), nullable=False),
        sa.Column(
            "current_rank",
            postgresql.ENUM(*RANKS, name="valorant_rank", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "main_roles",
            postgresql.ARRAY(
                postgresql.ENUM(*ROLES, name="valorant_role", create_type=False)
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(*STATUSES, name="player_status", create_type=False),
            server_default="OFFLINE",
            nullable=False,
        ),
        sa.Column(
            "teammate_rating",
            sa.Numeric(precision=3, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("reviews_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "cardinality(main_roles) > 0",
            name="main_roles_not_empty",
        ),
        sa.CheckConstraint(
            "length(btrim(region)) > 0",
            name="region_not_blank",
        ),
        sa.CheckConstraint(
            "reviews_count >= 0",
            name="reviews_count_non_negative",
        ),
        sa.CheckConstraint(
            "teammate_rating >= 0 AND teammate_rating <= 5",
            name="teammate_rating_range",
        ),
        sa.CheckConstraint(
            "reviews_count <> 0 OR teammate_rating = 0",
            name="zero_reviews_zero_rating",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], name="fk_valorant_profiles_player_id_players", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_valorant_profiles"),
        sa.UniqueConstraint("player_id", name="uq_valorant_profiles_player_id"),
    )
    op.create_index(
        "ix_valorant_profiles_matchmaking_filters",
        "valorant_profiles",
        ["region", "status", "current_rank", "teammate_rating"],
    )
    op.create_index(
        "ix_valorant_profiles_main_roles_gin",
        "valorant_profiles",
        ["main_roles"],
        postgresql_using="gin",
    )

    op.create_table(
        "teammate_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_player_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "reviewer_id <> target_player_id",
            name="not_self_review",
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="rating_range",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"], ["players.id"], name="fk_teammate_reviews_reviewer_id_players", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["target_player_id"], ["players.id"], name="fk_teammate_reviews_target_player_id_players", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_teammate_reviews"),
    )
    op.create_index(
        "ix_teammate_reviews_reviewer_id",
        "teammate_reviews",
        ["reviewer_id"],
    )
    op.create_index(
        "ix_teammate_reviews_target_player_id",
        "teammate_reviews",
        ["target_player_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_teammate_reviews_target_player_id", table_name="teammate_reviews")
    op.drop_index("ix_teammate_reviews_reviewer_id", table_name="teammate_reviews")
    op.drop_table("teammate_reviews")

    op.drop_index("ix_valorant_profiles_main_roles_gin", table_name="valorant_profiles")
    op.drop_index("ix_valorant_profiles_matchmaking_filters", table_name="valorant_profiles")
    op.drop_table("valorant_profiles")
    op.drop_table("players")

    bind = op.get_bind()
    postgresql.ENUM(*STATUSES, name="player_status").drop(bind, checkfirst=True)
    postgresql.ENUM(*ROLES, name="valorant_role").drop(bind, checkfirst=True)
    postgresql.ENUM(*RANKS, name="valorant_rank").drop(bind, checkfirst=True)
