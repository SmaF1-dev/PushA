package domain

import "testing"

func TestIsValidValorantRank(t *testing.T) {
	tests := []struct {
		name     string
		rank     string
		expected bool
	}{
		{name: "valid low rank", rank: "IRON_1", expected: true},
		{name: "valid middle rank", rank: "GOLD_2", expected: true},
		{name: "valid top rank", rank: "RADIANT", expected: true},
		{name: "invalid rank", rank: "WOOD_1", expected: false},
		{name: "empty rank", rank: "", expected: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsValidValorantRank(tt.rank)
			if got != tt.expected {
				t.Fatalf("expected %v, got %v", tt.expected, got)
			}
		})
	}
}

func TestIsRankRangeValid(t *testing.T) {
	tests := []struct {
		name     string
		minRank  string
		maxRank  string
		expected bool
	}{
		{name: "valid range", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: true},
		{name: "same rank", minRank: "GOLD_1", maxRank: "GOLD_1", expected: true},
		{name: "invalid reversed range", minRank: "PLATINUM_3", maxRank: "GOLD_1", expected: false},
		{name: "invalid min rank", minRank: "WOOD_1", maxRank: "GOLD_1", expected: false},
		{name: "invalid max rank", minRank: "GOLD_1", maxRank: "WOOD_1", expected: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsRankRangeValid(tt.minRank, tt.maxRank)
			if got != tt.expected {
				t.Fatalf("expected %v, got %v", tt.expected, got)
			}
		})
	}
}

func TestIsRankInRange(t *testing.T) {
	tests := []struct {
		name     string
		rank     string
		minRank  string
		maxRank  string
		expected bool
	}{
		{name: "rank inside range", rank: "GOLD_2", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: true},
		{name: "rank equals min", rank: "GOLD_1", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: true},
		{name: "rank equals max", rank: "PLATINUM_3", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: true},
		{name: "rank below range", rank: "SILVER_3", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: false},
		{name: "rank above range", rank: "DIAMOND_1", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: false},
		{name: "invalid rank", rank: "WOOD_1", minRank: "GOLD_1", maxRank: "PLATINUM_3", expected: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsRankInRange(tt.rank, tt.minRank, tt.maxRank)
			if got != tt.expected {
				t.Fatalf("expected %v, got %v", tt.expected, got)
			}
		})
	}
}

func TestIsValidValorantRole(t *testing.T) {
	if !IsValidValorantRole("CONTROLLER") {
		t.Fatalf("expected CONTROLLER to be valid")
	}

	if IsValidValorantRole("SNIPER") {
		t.Fatalf("expected SNIPER to be invalid")
	}
}

func TestIsValidPlayerStatus(t *testing.T) {
	if !IsValidPlayerStatus("READY_TO_PLAY") {
		t.Fatalf("expected READY_TO_PLAY to be valid")
	}

	if IsValidPlayerStatus("SLEEPING") {
		t.Fatalf("expected SLEEPING to be invalid")
	}
}

func TestIsValidMatchingStrategy(t *testing.T) {
	if !IsValidMatchingStrategy("BALANCED") {
		t.Fatalf("expected BALANCED to be valid")
	}

	if IsValidMatchingStrategy("RANDOM") {
		t.Fatalf("expected RANDOM to be invalid")
	}
}
