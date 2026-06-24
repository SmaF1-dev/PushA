RIOT_ID_UNIQUE_CONSTRAINT = "uq_players_riot_id"


def find_constraint_name(error: BaseException) -> str | None:
    """Find a PostgreSQL constraint name in a wrapped database exception.

    SQLAlchemy and ``asyncpg`` wrap driver exceptions at several levels. The
    traversal is deliberately bounded and cycle-safe.

    :param error: Top-level database exception.
    :returns: Constraint name or ``None`` when it cannot be determined.
    """
    current: BaseException | None = error
    visited: set[int] = set()

    while current is not None and id(current) not in visited:
        visited.add(id(current))
        constraint_name = getattr(current, "constraint_name", None)
        if isinstance(constraint_name, str):
            return constraint_name

        current = (
            getattr(current, "orig", None)
            or current.__cause__
            or current.__context__
        )

    return None
