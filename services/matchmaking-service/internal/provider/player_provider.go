package provider

import (
	"context"
	"pusha/matchmaking-service/internal/domain"
)

// FindPlayersRequest contains search constraints used by the matchmaking service
// to request suitable Valorant players from an external player source.
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

// PlayerProvider describes a source of Valorant players for matchmaking.
//
// The matchmaking service uses this interface instead of depending on a concrete
// data source. In local mode it can be implemented by a mock provider, while in
// integrated mode it is implemented by a gRPC client to the Python Player Service.
type PlayerProvider interface {
	FindPlayers(ctx context.Context, request FindPlayersRequest) ([]domain.Candidate, error)
}
