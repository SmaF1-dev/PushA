from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import PlayerStatus, ValorantRank, ValorantRole
from .player import PlayerModel


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [str(member.value) for member in enum_class]


valorant_rank_enum = SAEnum(
    ValorantRank,
    name="valorant_rank",
    values_callable=enum_values,
    validate_strings=True,
)
valorant_role_enum = SAEnum(
    ValorantRole,
    name="valorant_role",
    values_callable=enum_values,
    validate_strings=True,
)
player_status_enum = SAEnum(
    PlayerStatus,
    name="player_status",
    values_callable=enum_values,
    validate_strings=True,
)


class ValorantProfileModel(Base):
    __tablename__ = "valorant_profiles"
    __table_args__ = (
        UniqueConstraint("player_id"),
        CheckConstraint("length(btrim(region)) > 0", name="region_not_blank"),
        CheckConstraint("cardinality(main_roles) > 0", name="main_roles_not_empty"),
        CheckConstraint(
            "teammate_rating >= 0 AND teammate_rating <= 5",
            name="teammate_rating_range",
        ),
        CheckConstraint("reviews_count >= 0", name="reviews_count_non_negative"),
        CheckConstraint(
            "reviews_count <> 0 OR teammate_rating = 0",
            name="zero_reviews_zero_rating",
        ),
        Index(
            "ix_valorant_profiles_matchmaking_filters",
            "region",
            "status",
            "current_rank",
            "teammate_rating",
        ),
        Index(
            "ix_valorant_profiles_main_roles_gin",
            "main_roles",
            postgresql_using="gin",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    player_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    region: Mapped[str] = mapped_column(String(32), nullable=False)
    current_rank: Mapped[ValorantRank] = mapped_column(
        valorant_rank_enum, nullable=False
    )
    main_roles: Mapped[list[ValorantRole]] = mapped_column(
        ARRAY(valorant_role_enum), nullable=False
    )
    status: Mapped[PlayerStatus] = mapped_column(
        player_status_enum,
        nullable=False,
        default=PlayerStatus.OFFLINE,
        server_default=str(PlayerStatus.OFFLINE.value),
    )
    teammate_rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.00"), server_default="0.00"
    )
    reviews_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    player: Mapped[PlayerModel] = relationship(back_populates="profile")
