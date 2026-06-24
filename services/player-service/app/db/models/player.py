from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .teammate_review import TeammateReviewModel


class PlayerModel(Base):
    """Persist a player account.

    :ivar id: Stable player UUID.
    :ivar nickname: Display name used by the player.
    :ivar riot_id: Globally unique Riot identifier.
    :ivar created_at: Creation timestamp.
    :ivar updated_at: Last modification timestamp.
    """

    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("riot_id"),
        CheckConstraint("length(btrim(nickname)) > 0", name="nickname_not_blank"),
        CheckConstraint("length(btrim(riot_id)) > 0", name="riot_id_not_blank"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    nickname: Mapped[str] = mapped_column(String(100), nullable=False)
    riot_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    profile: Mapped["ValorantProfileModel | None"] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    reviews_written: Mapped[list["TeammateReviewModel"]] = relationship(
        back_populates="reviewer",
        cascade="all, delete-orphan",
        foreign_keys="TeammateReviewModel.reviewer_id",
        passive_deletes=True,
    )
    reviews_received: Mapped[list["TeammateReviewModel"]] = relationship(
        back_populates="target_player",
        cascade="all, delete-orphan",
        foreign_keys="TeammateReviewModel.target_player_id",
        passive_deletes=True,
    )
