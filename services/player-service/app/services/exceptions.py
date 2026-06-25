from uuid import UUID


class ServiceError(Exception):
    """Base class for expected application-layer failures."""


class PlayerNotFoundError(ServiceError):
    """Report that a requested player does not exist.

    :param player_id: Missing player UUID.
    """

    def __init__(self, player_id: UUID) -> None:
        self.player_id = player_id
        super().__init__(f"player {player_id} was not found")


class ProfileNotFoundError(ServiceError):
    """Report that a requested Valorant profile does not exist.

    :param player_id: UUID of the player whose profile is missing.
    """

    def __init__(self, player_id: UUID) -> None:
        self.player_id = player_id
        super().__init__(f"Valorant profile for player {player_id} was not found")


class RiotIdAlreadyExistsError(ServiceError):
    """Report an attempt to register a duplicate Riot ID.

    :param riot_id: Riot identifier that is already registered.
    """

    def __init__(self, riot_id: str) -> None:
        self.riot_id = riot_id
        super().__init__(f"Riot ID {riot_id!r} is already registered")
