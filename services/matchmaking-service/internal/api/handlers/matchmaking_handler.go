package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"pusha/matchmaking-service/internal/api/response"
	"pusha/matchmaking-service/internal/domain"
	"pusha/matchmaking-service/internal/dto"
	"pusha/matchmaking-service/internal/service"
	"time"

	"github.com/go-chi/chi/v5"
)

type MatchmakingHandler struct {
	matchmakingService *service.MatchmakingService
}

func NewMatchmakingHandler(matchmakingService *service.MatchmakingService) *MatchmakingHandler {
	return &MatchmakingHandler{
		matchmakingService: matchmakingService,
	}
}

func (h *MatchmakingHandler) CreateMatchmakingRequestHandler(w http.ResponseWriter, r *http.Request) {
	var request dto.CreateMatchmakingRequest

	err := json.NewDecoder(r.Body).Decode(&request)
	if err != nil {
		response.WriteError(w, http.StatusBadRequest, "INVALID_JSON", "Request body contains invalid JSON", nil)
		return
	}

	matchmakingRequest, err := h.matchmakingService.CreateRequest(r.Context(), request)
	if err != nil {
		writeCreateRequestError(w, err)
		return
	}

	response.WriteJSON(w, http.StatusCreated, toMatchmakingRequestResponse(matchmakingRequest))
}

func (h *MatchmakingHandler) GetMatchmakingRequestHandler(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "request_id")
	if requestID == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "request_id is required", map[string]any{
			"field": "request_id",
		})
		return
	}

	matchmakingRequest, err := h.matchmakingService.GetRequestByID(r.Context(), requestID)
	if err != nil {
		response.WriteError(w, http.StatusNotFound, "MATCHMAKING_REQUEST_NOT_FOUND", "Matchmaking request not found", map[string]any{
			"request_id": requestID,
		})
		return
	}
	response.WriteJSON(w, http.StatusOK, toMatchmakingRequestResponse(matchmakingRequest))
}

func (h *MatchmakingHandler) GetPlayerMatchmakingRequestsHandler(w http.ResponseWriter, r *http.Request) {
	playerID := chi.URLParam(r, "player_id")
	if playerID == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "player_id is required", map[string]any{
			"field": "player_id",
		})
		return
	}

	requests, err := h.matchmakingService.GetRequestsByAuthorID(r.Context(), playerID)
	if err != nil {
		response.WriteError(w, http.StatusInternalServerError, "DATABASE_ERROR", "Failed to get player matchmaking requests", map[string]any{
			"reason": err.Error(),
		})
		return
	}

	requestResponses := make([]dto.MatchmakingRequestResponse, 0, len(requests))
	for _, request := range requests {
		requestResponses = append(requestResponses, toMatchmakingRequestResponse(request))
	}

	response.WriteJSON(w, http.StatusOK, dto.PlayerMatchmakingRequestsResponse{
		PlayerID: playerID,
		Requests: requestResponses,
	})
}

func writeCreateRequestError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, service.ErrAuthorIDRequired):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "author_id"})
	case errors.Is(err, service.ErrMinRankRequired):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "min_rank"})
	case errors.Is(err, service.ErrInvalidMinRank):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "min_rank"})
	case errors.Is(err, service.ErrMaxRankRequired):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "max_rank"})
	case errors.Is(err, service.ErrInvalidMaxRank):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "max_rank"})
	case errors.Is(err, service.ErrInvalidRankRange):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "rank_range"})
	case errors.Is(err, service.ErrRequiredPlayerStatusRequired):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "required_player_status"})
	case errors.Is(err, service.ErrInvalidRequiredPlayerStatus):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "required_player_status"})
	case errors.Is(err, service.ErrInvalidMinTeammateRating):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "min_teammate_rating"})
	case errors.Is(err, service.ErrRegionRequired):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "region"})
	case errors.Is(err, service.ErrInvalidRequiredRole):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "required_roles"})
	case errors.Is(err, service.ErrInvalidNeededPlayers):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "needed_players"})
	case errors.Is(err, service.ErrStrategyRequired):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "strategy"})
	case errors.Is(err, service.ErrInvalidStrategy):
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), map[string]any{"field": "strategy"})
	case errors.Is(err, service.ErrActiveRequestAlreadyExists):
		response.WriteError(w, http.StatusConflict, "ACTIVE_REQUEST_ALREADY_EXISTS", err.Error(), nil)
	default:
		response.WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to create matchmaking request", map[string]any{
			"reason": err.Error(),
		})
	}
}

func toMatchmakingRequestResponse(request domain.MatchmakingRequest) dto.MatchmakingRequestResponse {
	return dto.MatchmakingRequestResponse{
		ID:                   request.ID,
		AuthorID:             request.AuthorID,
		MinRank:              request.MinRank,
		MaxRank:              request.MaxRank,
		RequiredPlayerStatus: request.RequiredPlayerStatus,
		MinTeammateRating:    request.MinTeammateRating,
		Region:               request.Region,
		RequiredRoles:        request.RequiredRoles,
		NeededPlayers:        request.NeededPlayers,
		Strategy:             request.Strategy,
		Status:               request.Status,
		CreatedAt:            request.CreatedAt.Format(time.RFC3339),
		ExpiresAt:            request.ExpiresAt.Format(time.RFC3339),
	}
}
