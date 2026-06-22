from enum import StrEnum


class ValorantRole(StrEnum):
    DUELIST = "DUELIST"
    CONTROLLER = "CONTROLLER"
    INITIATOR = "INITIATOR"
    SENTINEL = "SENTINEL"


class PlayerStatus(StrEnum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    READY_TO_PLAY = "READY_TO_PLAY"
    IN_GAME = "IN_GAME"
    BUSY = "BUSY"


class ValorantRank(StrEnum):
    IRON_1 = "IRON_1"
    IRON_2 = "IRON_2"
    IRON_3 = "IRON_3"
    BRONZE_1 = "BRONZE_1"
    BRONZE_2 = "BRONZE_2"
    BRONZE_3 = "BRONZE_3"
    SILVER_1 = "SILVER_1"
    SILVER_2 = "SILVER_2"
    SILVER_3 = "SILVER_3"
    GOLD_1 = "GOLD_1"
    GOLD_2 = "GOLD_2"
    GOLD_3 = "GOLD_3"
    PLATINUM_1 = "PLATINUM_1"
    PLATINUM_2 = "PLATINUM_2"
    PLATINUM_3 = "PLATINUM_3"
    DIAMOND_1 = "DIAMOND_1"
    DIAMOND_2 = "DIAMOND_2"
    DIAMOND_3 = "DIAMOND_3"
    ASCENDANT_1 = "ASCENDANT_1"
    ASCENDANT_2 = "ASCENDANT_2"
    ASCENDANT_3 = "ASCENDANT_3"
    IMMORTAL_1 = "IMMORTAL_1"
    IMMORTAL_2 = "IMMORTAL_2"
    IMMORTAL_3 = "IMMORTAL_3"
    RADIANT = "RADIANT"

    @property
    def order(self) -> int:
        """Return the rank's position in the hierarchy."""
        return tuple(type(self)).index(self)

    def is_between_or_equal(self, minimum: "ValorantRank", maximum: "ValorantRank") -> bool:
        """
        Check whether this rank belongs to given rank range
        :param minimum: the lowest possible rank
        :param maximum: the highest possible rank
        :return: True if rank belongs to given range False otherwise
        """
        if minimum.order > maximum.order:
            raise ValueError("minimum rank cannot be higher than maximum rank")
        return minimum.order <= self.order <= maximum.order
