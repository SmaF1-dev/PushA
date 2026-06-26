package provider

import (
	"testing"

	playerpb "pusha/matchmaking-service/pkg/proto"
)

func TestMapGrpcCandidateToDomainCandidate(t *testing.T) {
	grpcCandidate := &playerpb.ValorantPlayerCandidate{
		PlayerId:       "player-uuid-1",
		Nickname:       "GrpcTestPlayer001",
		RiotId:         "grpc-test-001#SEED",
		Region:         "EU",
		CurrentRank:    "GOLD_2",
		MainRoles:      []string{"CONTROLLER", "SENTINEL"},
		Status:         "READY_TO_PLAY",
		TeammateRating: 4.67,
		ReviewsCount:   10,
	}

	candidate := mapGrpcCandidateToDomainCandidate(grpcCandidate)

	if candidate.ID == "" {
		t.Fatalf("expected internal candidate ID to be generated")
	}

	if candidate.PlayerID != "player-uuid-1" {
		t.Fatalf("expected player-uuid-1, got %s", candidate.PlayerID)
	}

	if candidate.Nickname != "GrpcTestPlayer001" {
		t.Fatalf("unexpected nickname: %s", candidate.Nickname)
	}

	if candidate.RiotID != "grpc-test-001#SEED" {
		t.Fatalf("unexpected riot id: %s", candidate.RiotID)
	}

	if candidate.CurrentRank != "GOLD_2" {
		t.Fatalf("unexpected rank: %s", candidate.CurrentRank)
	}

	if candidate.Region != "EU" {
		t.Fatalf("unexpected region: %s", candidate.Region)
	}

	if len(candidate.MainRoles) != 2 {
		t.Fatalf("expected 2 roles, got %d", len(candidate.MainRoles))
	}

	if candidate.Status != "READY_TO_PLAY" {
		t.Fatalf("unexpected status: %s", candidate.Status)
	}

	if candidate.TeammateRating != 4.67 {
		t.Fatalf("unexpected rating: %.2f", candidate.TeammateRating)
	}

	if candidate.CreatedAt.IsZero() {
		t.Fatalf("expected CreatedAt to be set")
	}
}
