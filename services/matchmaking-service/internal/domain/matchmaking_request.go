package domain

import "time"

type MatchmakingRequest struct {
	ID                   string
	AuthorID             string
	MinRank              string
	MaxRank              string
	RequiredPlayerStatus string
	MinTeammateRating    float64
	Region               string
	RequiredRoles        []string
	NeededPlayers        int
	Strategy             string
	Status               string
	CreatedAt            time.Time
	ExpiresAt            time.Time
}

const (
	MatchmakingRequestStatusOpen      = "OPEN"
	MatchmakingRequestStatusSearching = "SEARCHING"
	MatchmakingRequestStatusCompleted = "COMPLETED"
	MatchmakingRequestStatusCancelled = "CANCELLED"
	MatchmakingRequestStatusExpired   = "EXPIRED"
)
