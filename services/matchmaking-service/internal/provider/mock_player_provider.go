package provider

import (
	"context"
	"pusha/matchmaking-service/internal/domain"
	"time"

	"github.com/google/uuid"
)

type MockPlayerProvider struct{}

func NewMockPlayerProvider() *MockPlayerProvider {
	return &MockPlayerProvider{}
}

func (p *MockPlayerProvider) FindPlayers(ctx context.Context, request FindPlayersRequest) ([]domain.Candidate, error) {
	now := time.Now().UTC()

	candidates := []domain.Candidate{
		{
			ID:             uuid.NewString(),
			PlayerID:       "player_2",
			Nickname:       "SmokeMaster",
			RiotID:         "SmokeMaster#EUW",
			CurrentRank:    "GOLD_2",
			Region:         request.Region,
			MainRoles:      []string{"CONTROLLER"},
			Status:         "READY_TO_PLAY",
			TeammateRating: 4.5,
			CreatedAt:      now,
		},
		{
			ID:             uuid.NewString(),
			PlayerID:       "player_3",
			Nickname:       "SentinelGuy",
			RiotID:         "SentinelGuy#EUW",
			CurrentRank:    "PLATINUM_1",
			Region:         request.Region,
			MainRoles:      []string{"SENTINEL"},
			Status:         "READY_TO_PLAY",
			TeammateRating: 4.2,
			CreatedAt:      now,
		},
		{
			ID:             uuid.NewString(),
			PlayerID:       "player_4",
			Nickname:       "FlashBoy",
			RiotID:         "FlashBoy#EUW",
			CurrentRank:    "GOLD_3",
			Region:         request.Region,
			MainRoles:      []string{"INITIATOR"},
			Status:         "READY_TO_PLAY",
			TeammateRating: 3.9,
			CreatedAt:      now,
		},
		{
			ID:             uuid.NewString(),
			PlayerID:       "player_5",
			Nickname:       "DuelOnly",
			RiotID:         "DuelOnly#EUW",
			CurrentRank:    "SILVER_2",
			Region:         request.Region,
			MainRoles:      []string{"DUELIST"},
			Status:         "ONLINE",
			TeammateRating: 4.8,
			CreatedAt:      now,
		},
	}

	return candidates, nil
}
