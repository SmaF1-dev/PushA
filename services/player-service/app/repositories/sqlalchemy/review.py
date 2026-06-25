from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TeammateReviewModel
from app.domain import TeammateReview
from app.repositories.interfaces import ReviewRepository
from app.repositories.mappers import review_to_domain, review_to_model


class SqlAlchemyReviewRepository(ReviewRepository):
    """Persist teammate reviews through an asynchronous SQLAlchemy session.

    :param session: Session used for all repository operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, review: TeammateReview) -> TeammateReview:
        """Persist a review without committing the transaction.

        :param review: Domain review to persist.
        :returns: Persisted review.
        :raises sqlalchemy.exc.IntegrityError: If a database constraint is violated.
        """
        model = review_to_model(review)
        self._session.add(model)
        await self._session.flush()
        return review_to_domain(model)

    async def get_by_id(self, review_id: UUID) -> TeammateReview | None:
        """Find a review by ID.

        :param review_id: Review UUID.
        :returns: Review or ``None`` when absent.
        """
        model = await self._session.get(TeammateReviewModel, review_id)
        return review_to_domain(model) if model is not None else None

    async def list_for_target(
        self,
        target_player_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[TeammateReview]:
        """List reviews received by a player.

        :param target_player_id: UUID of the reviewed player.
        :param limit: Maximum number of reviews to return.
        :param offset: Number of reviews to skip.
        :returns: Reviews ordered from newest to oldest.
        """
        statement = (
            select(TeammateReviewModel)
            .where(TeammateReviewModel.target_player_id == target_player_id)
            .order_by(
                TeammateReviewModel.created_at.desc(),
                TeammateReviewModel.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        models = (await self._session.scalars(statement)).all()
        return [review_to_domain(model) for model in models]

    async def list_ratings_for_target(self, target_player_id: UUID) -> Sequence[int]:
        """List ratings received by a player.

        :param target_player_id: UUID of the reviewed player.
        :returns: Integer ratings used by the domain aggregate.
        """
        statement = select(TeammateReviewModel.rating).where(
            TeammateReviewModel.target_player_id == target_player_id
        )
        return list((await self._session.scalars(statement)).all())
