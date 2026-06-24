from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from .player import PlayerModel


class TeammateReviewModel(Base):
    """Persist a review written by one player about another.

    :ivar reviewer_id: UUID of the player who wrote the review.
    :ivar target_player_id: UUID of the reviewed player.
    :ivar rating: Integer rating from one to five.
    :ivar comment: Optional review text.
    :ivar created_at: Review creation timestamp.
    """

    __tablename__ = "teammate_reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
        CheckConstraint("reviewer_id <> target_player_id", name="not_self_review"),
        Index("ix_teammate_reviews_reviewer_id", "reviewer_id"),
        Index("ix_teammate_reviews_target_player_id", "target_player_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    reviewer_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_player_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reviewer: Mapped[PlayerModel] = relationship(
        back_populates="reviews_written", foreign_keys=[reviewer_id]
    )
    target_player: Mapped[PlayerModel] = relationship(
        back_populates="reviews_received", foreign_keys=[target_player_id]
    )
