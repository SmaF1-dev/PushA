package domain

import "time"

type Candidate struct {
	ID             string
	RequestID      string
	PlayerID       string
	Nickname       string
	RiotID         string
	CurrentRank    string
	Region         string
	MainRoles      []string
	Status         string
	TeammateRating float64
	Score          float64
	CreatedAt      time.Time
}
