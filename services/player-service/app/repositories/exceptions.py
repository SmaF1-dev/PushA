class RepositoryError(Exception):
    """Base class for expected repository failures."""


class DuplicateRiotIdError(RepositoryError):
    """Report a Riot ID conflict detected by persistent storage.

    :param riot_id: Riot identifier that violates the uniqueness constraint.
    """

    def __init__(self, riot_id: str) -> None:
        self.riot_id = riot_id
        super().__init__(f"Riot ID {riot_id!r} already exists")
