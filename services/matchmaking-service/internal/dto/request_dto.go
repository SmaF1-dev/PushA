package dto

type CreateMatchmakingRequest struct {
	AuthorID             string   `json:"author_id"`
	MinRank              string   `json:"min_rank"`
	MaxRank              string   `json:"max_rank"`
	RequiredPlayerStatus string   `json:"required_player_status"`
	MinTeammateRating    float64  `json:"min_teammate_rating"`
	Region               string   `json:"region"`
	RequiredRoles        []string `json:"required_roles"`
	NeededPlayers        int      `json:"needed_players"`
	Strategy             string   `json:"strategy"`
}

type CreateMatchGroupRequest struct {
	SelectedCandidateIDs []string `json:"selected_candidate_ids"`
}
