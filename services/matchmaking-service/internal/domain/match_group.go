package domain

import "time"

type MatchGroup struct {
	ID        string
	RequestID string
	Members   []string
	Status    string
	CreatedAt time.Time
}

const (
	MatchGroupStatusCreated   = "CREATED"
	MatchGroupStatusConfirmed = "CONFIRMED"
	MatchGroupStatusExpired   = "EXPIRED"
)
