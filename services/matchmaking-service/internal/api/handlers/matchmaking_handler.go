package handlers

import (
	"encoding/json"
	"net/http"
	"pusha/matchmaking-service/internal/api/response"
	"pusha/matchmaking-service/internal/dto"
	"time"
)

func CreateMatchmakingRequestHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		response.WriteError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "Only POST method is allowed", nil)
		return
	}

	var request dto.CreateMatchmakingRequest

	err := json.NewDecoder(r.Body).Decode(&request)
	if err != nil {
		response.WriteError(w, http.StatusBadRequest, "INVALID_JSON", "Request body contains invalid JSON", nil)
		return
	}

	if request.AuthorID == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "author_id is required", map[string]any{
			"field": "author_id",
		})
		return
	}

	if request.MinRank == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "min_rank is required", map[string]any{
			"field": "min_rank",
		})
		return
	}

	if request.MaxRank == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "max_rank is required", map[string]any{
			"field": "max_rank",
		})
		return
	}

	if request.RequiredPlayerStatus == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "required_player_status is required", map[string]any{
			"field": "required_player_status",
		})
		return
	}

	if request.MinTeammateRating < 0 || request.MinTeammateRating > 5 {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "min_teammate_rating must be between 0 and 5", map[string]any{
			"field": "min_teammate_rating",
		})
		return
	}

	if request.Region == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "region is required", map[string]any{
			"field": "region",
		})
		return
	}

	if request.NeededPlayers < 1 || request.NeededPlayers > 4 {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "needed_players must be between 1 and 4", map[string]any{
			"field": "needed_players",
		})
		return
	}

	if request.Strategy == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "strategy is required", map[string]any{
			"field": "strategy",
		})
		return
	}

	now := time.Now().UTC()
	expiresAt := now.Add(time.Hour)

	result := dto.MatchmakingRequestResponse{
		ID:                   "request_mock_1",
		AuthorID:             request.AuthorID,
		MinRank:              request.MinRank,
		MaxRank:              request.MaxRank,
		RequiredPlayerStatus: request.RequiredPlayerStatus,
		MinTeammateRating:    request.MinTeammateRating,
		Region:               request.Region,
		RequiredRoles:        request.RequiredRoles,
		NeededPlayers:        request.NeededPlayers,
		Strategy:             request.Strategy,
		Status:               "OPEN",
		CreatedAt:            now.Format(time.RFC3339),
		ExpiresAt:            expiresAt.Format(time.RFC3339),
	}

	response.WriteJSON(w, http.StatusCreated, result)
}
