package service

import (
	"pusha/matchmaking-service/internal/domain"
	"testing"
)

func TestBalancedScoringStrategy_CalculateScore(t *testing.T) {
	request := domain.MatchmakingRequest{
		MinRank:       "GOLD_1",
		MaxRank:       "PLATINUM_3",
		RequiredRoles: []string{"CONTROLLER", "SENTINEL"},
	}

	candidate := domain.Candidate{
		CurrentRank:    "GOLD_2",
		MainRoles:      []string{"CONTROLLER"},
		Status:         "READY_TO_PLAY",
		TeammateRating: 4.5,
	}

	strategy := BalancedScoringStrategy{}

	score := strategy.CalculateScore(request, candidate)
	expected := 97.0

	if score != expected {
		t.Fatalf("expected score %.1f, got %.1f", expected, score)
	}
}

func TestBalancedScoringStrategy_CandidateWithWrongRoleGetsLowerScore(t *testing.T) {
	request := domain.MatchmakingRequest{
		MinRank:       "GOLD_1",
		MaxRank:       "PLATINUM_3",
		RequiredRoles: []string{"CONTROLLER", "SENTINEL"},
	}

	candidate := domain.Candidate{
		CurrentRank:    "GOLD_3",
		MainRoles:      []string{"INITIATOR"},
		Status:         "READY_TO_PLAY",
		TeammateRating: 3.9,
	}

	strategy := BalancedScoringStrategy{}

	score := strategy.CalculateScore(request, candidate)

	expected := 81.4
	if score != expected {
		t.Fatalf("expected score %.1f, got %.1f", expected, score)
	}
}

func TestNewScoringStrategy_ReturnsBalancedByDefault(t *testing.T) {
	strategy := NewScoringStrategy("UNKNOWN_STRATEGY")

	_, ok := strategy.(BalancedScoringStrategy)
	if !ok {
		t.Fatalf("expected BalancedScoringStrategy by default")
	}
}
