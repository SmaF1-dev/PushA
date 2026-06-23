package dto

type MatchmakingRequestResponse struct {
	ID                   string   `json:"id"`
	AuthorID             string   `json:"author_id"`
	MinRank              string   `json:"min_rank"`
	MaxRank              string   `json:"max_rank"`
	RequiredPlayerStatus string   `json:"required_player_status"`
	MinTeammateRating    float64  `json:"min_teammate_rating"`
	Region               string   `json:"region"`
	RequiredRoles        []string `json:"required_roles"`
	NeededPlayers        int      `json:"needed_players"`
	Strategy             string   `json:"strategy"`
	Status               string   `json:"status"`
	CreatedAt            string   `json:"created_at"`
	ExpiresAt            string   `json:"expires_at"`
}

type SearchCandidatesResponse struct {
	RequestID  string              `json:"request_id"`
	Candidates []CandidateResponse `json:"candidates"`
}

type CandidateResponse struct {
	PlayerID       string   `json:"player_id"`
	Nickname       string   `json:"nickname"`
	RiotID         string   `json:"riot_id"`
	CurrentRank    string   `json:"current_rank"`
	Region         string   `json:"region"`
	MainRoles      []string `json:"main_roles"`
	Status         string   `json:"status"`
	TeammateRating float64  `json:"teammate_rating"`
	Score          float64  `json:"score"`
}

type MatchGroupResponse struct {
	ID        string   `json:"id"`
	RequestID string   `json:"request_id"`
	Members   []string `json:"members"`
	Status    string   `json:"status"`
	CreatedAt string   `json:"created_at"`
}

type PlayerMatchmakingRequestsResponse struct {
	PlayerID string                       `json:"player_id"`
	Requests []MatchmakingRequestResponse `json:"requests"`
}
