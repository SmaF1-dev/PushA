package service

import (
	"testing"

	"pusha/matchmaking-service/internal/domain"
)

func TestCandidateFilter_FiltersInvalidCandidates(t *testing.T) {
	request := domain.MatchmakingRequest{
		AuthorID:             "player_1",
		MinRank:              "GOLD_1",
		MaxRank:              "PLATINUM_3",
		RequiredPlayerStatus: "READY_TO_PLAY",
		MinTeammateRating:    4.0,
		Region:               "EU",
		RequiredRoles:        []string{"CONTROLLER", "SENTINEL"},
	}

	candidates := []domain.Candidate{
		{
			PlayerID:       "player_2",
			CurrentRank:    "GOLD_2",
			Status:         "READY_TO_PLAY",
			TeammateRating: 4.5,
			Region:         "EU",
			MainRoles:      []string{"CONTROLLER"},
		},
		{
			PlayerID:       "player_3",
			CurrentRank:    "SILVER_2",
			Status:         "ONLINE",
			TeammateRating: 4.8,
			Region:         "EU",
			MainRoles:      []string{"DUELIST"},
		},
		{
			PlayerID:       "player_1",
			CurrentRank:    "GOLD_2",
			Status:         "READY_TO_PLAY",
			TeammateRating: 4.5,
			Region:         "EU",
			MainRoles:      []string{"CONTROLLER"},
		},
	}

	filter := NewCandidateFilter()

	filteredCandidates := filter.Filter(request, candidates)

	if len(filteredCandidates) != 1 {
		t.Fatalf("expected 1 candidate, got %d", len(filteredCandidates))
	}

	if filteredCandidates[0].PlayerID != "player_2" {
		t.Fatalf("expected player_2, got %s", filteredCandidates[0].PlayerID)
	}
}

func TestRoleSpecification_AllowsAnyRoleWhenRequiredRolesEmpty(t *testing.T) {
	request := domain.MatchmakingRequest{
		RequiredRoles: []string{},
	}

	candidate := domain.Candidate{
		MainRoles: []string{"DUELIST"},
	}

	specification := RoleSpecification{}

	if !specification.IsSatisfiedBy(request, candidate) {
		t.Fatalf("expected candidate to satisfy role specification")
	}
}
