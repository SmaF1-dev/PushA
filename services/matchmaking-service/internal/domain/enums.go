package domain

var valorantRankOrder = map[string]int{
	"IRON_1": 1,
	"IRON_2": 2,
	"IRON_3": 3,

	"BRONZE_1": 4,
	"BRONZE_2": 5,
	"BRONZE_3": 6,

	"SILVER_1": 7,
	"SILVER_2": 8,
	"SILVER_3": 9,

	"GOLD_1": 10,
	"GOLD_2": 11,
	"GOLD_3": 12,

	"PLATINUM_1": 13,
	"PLATINUM_2": 14,
	"PLATINUM_3": 15,

	"DIAMOND_1": 16,
	"DIAMOND_2": 17,
	"DIAMOND_3": 18,

	"ASCENDANT_1": 19,
	"ASCENDANT_2": 20,
	"ASCENDANT_3": 21,

	"IMMORTAL_1": 22,
	"IMMORTAL_2": 23,
	"IMMORTAL_3": 24,

	"RADIANT": 25,
}

var validValorantRoles = map[string]struct{}{
	"DUELIST":    {},
	"CONTROLLER": {},
	"INITIATOR":  {},
	"SENTINEL":   {},
}

var validPlayerStatuses = map[string]struct{}{
	"OFFLINE":       {},
	"ONLINE":        {},
	"READY_TO_PLAY": {},
	"IN_GAME":       {},
	"BUSY":          {},
}

var validMatchingStrategies = map[string]struct{}{
	"BALANCED":       {},
	"RANK_FOCUSED":   {},
	"RATING_FOCUSED": {},
	"ROLE_FOCUSED":   {},
}

func IsValidValorantRank(rank string) bool {
	_, ok := valorantRankOrder[rank]
	return ok
}

func IsValidValorantRole(role string) bool {
	_, ok := validValorantRoles[role]
	return ok
}

func IsValidPlayerStatus(status string) bool {
	_, ok := validPlayerStatuses[status]
	return ok
}

func IsValidMatchingStrategy(strategy string) bool {
	_, ok := validMatchingStrategies[strategy]
	return ok
}

func IsRankRangeValid(minRank string, maxRank string) bool {
	minRankOrder, minRankExists := valorantRankOrder[minRank]
	maxRankOrder, maxRankExists := valorantRankOrder[maxRank]

	if !minRankExists || !maxRankExists {
		return false
	}

	return minRankOrder <= maxRankOrder
}

func IsRankInRange(rank string, minRank string, maxRank string) bool {
	rankOrder, rankExists := valorantRankOrder[rank]
	minRankOrder, minRankExists := valorantRankOrder[minRank]
	maxRankOrder, maxRankExists := valorantRankOrder[maxRank]

	if !rankExists || !minRankExists || !maxRankExists {
		return false
	}

	return rankOrder >= minRankOrder && rankOrder <= maxRankOrder
}
