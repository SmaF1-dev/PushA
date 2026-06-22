package handlers

import (
	"encoding/json"
	"net/http"
	"pusha/matchmaking-service/internal/api/response"
	"pusha/matchmaking-service/internal/domain"
	"pusha/matchmaking-service/internal/dto"
	"pusha/matchmaking-service/internal/repository"
	"time"

	"github.com/google/uuid"
)

type MatchmakingHandler struct {
	matchmakingRepository *repository.MatchmakingRepository
}

func NewMatchmakingHandler(matchmakingRepository *repository.MatchmakingRepository) *MatchmakingHandler {
	return &MatchmakingHandler{
		matchmakingRepository: matchmakingRepository,
	}
}

func (h *MatchmakingHandler) CreateMatchmakingRequestHandler(w http.ResponseWriter, r *http.Request) {
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

	matchmakingRequest := domain.MatchmakingRequest{
		ID:                   uuid.NewString(),
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
		CreatedAt:            now,
		ExpiresAt:            expiresAt,
	}

	err = h.matchmakingRepository.Create(r.Context(), matchmakingRequest)
	if err != nil {
		response.WriteError(w, http.StatusInternalServerError, "DATABASE_ERROR", "Failed to create matchmaking request", map[string]any{
			"reason": err.Error(),
		})
		return
	}

	result := dto.MatchmakingRequestResponse{
		ID:                   matchmakingRequest.ID,
		AuthorID:             matchmakingRequest.AuthorID,
		MinRank:              matchmakingRequest.MinRank,
		MaxRank:              matchmakingRequest.MaxRank,
		RequiredPlayerStatus: matchmakingRequest.RequiredPlayerStatus,
		MinTeammateRating:    matchmakingRequest.MinTeammateRating,
		Region:               matchmakingRequest.Region,
		RequiredRoles:        matchmakingRequest.RequiredRoles,
		NeededPlayers:        matchmakingRequest.NeededPlayers,
		Strategy:             matchmakingRequest.Strategy,
		Status:               matchmakingRequest.Status,
		CreatedAt:            matchmakingRequest.CreatedAt.Format(time.RFC3339),
		ExpiresAt:            matchmakingRequest.ExpiresAt.Format(time.RFC3339),
	}

	response.WriteJSON(w, http.StatusCreated, result)
}
