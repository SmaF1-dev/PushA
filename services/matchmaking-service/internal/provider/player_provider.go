package provider

import (
	"context"
	"pusha/matchmaking-service/internal/domain"
)

type FindPlayersRequest struct {
	ExcludedPlayerID     string
	MinRank              string
	MaxRank              string
	RequiredPlayerStatus string
	MinTeammateRating    float64
	Region               string
	RequiredRoles        []string
	Limit                int
}

type PlayerProvider interface {
	FindPlayers(ctx context.Context, request FindPlayersRequest) ([]domain.Candidate, error)
}
