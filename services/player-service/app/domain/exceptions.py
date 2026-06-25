"""Exceptions raised when a domain invariant is violated."""


class DomainError(ValueError):
    """Base error for invalid domain state or operations."""


class InvalidPlayerError(DomainError):
    """Player data is invalid."""


class InvalidProfileError(DomainError):
    """Valorant profile data is invalid."""


class InvalidReviewError(DomainError):
    """Teammate review data is invalid."""


class InvalidPlayerQueryError(DomainError):
    """Player search or eligibility criteria are invalid."""
