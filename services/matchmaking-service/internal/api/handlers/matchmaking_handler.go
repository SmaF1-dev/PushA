package handlers

import (
	"context"
	"encoding/json"
	"net/http"
	"pusha/matchmaking-service/internal/api/response"
	"pusha/matchmaking-service/internal/domain"
	"pusha/matchmaking-service/internal/dto"
	"time"

	"github.com/go-chi/chi/v5"
)

type MatchmakingService interface {
	CreateRequest(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error)
	GetRequestByID(ctx context.Context, requestID string) (domain.MatchmakingRequest, error)
	GetRequestsByAuthorID(ctx context.Context, authorID string) ([]domain.MatchmakingRequest, error)
	SearchCandidates(ctx context.Context, requestID string) ([]domain.Candidate, error)
	GetCandidatesByRequestID(ctx context.Context, requestID string) ([]domain.Candidate, error)
	CreateGroup(ctx context.Context, requestID string, selectedCandidateIDs []string) (domain.MatchGroup, error)
}

type MatchmakingHandler struct {
	matchmakingService MatchmakingService
}

func NewMatchmakingHandler(matchmakingService MatchmakingService) *MatchmakingHandler {
	return &MatchmakingHandler{
		matchmakingService: matchmakingService,
	}
}

// CreateMatchmakingRequestHandler creates a new matchmaking request.
//
// @Summary Create matchmaking request
// @Description Creates a new Valorant matchmaking request for a player.
// @Tags Matchmaking Requests
// @Accept json
// @Produce json
// @Param request body dto.CreateMatchmakingRequest true "Create matchmaking request"
// @Success 201 {object} dto.MatchmakingRequestResponse
// @Failure 400 {object} response.ErrorResponse
// @Failure 409 {object} response.ErrorResponse
// @Failure 500 {object} response.ErrorResponse
// @Router /matchmaking/requests [post]
func (h *MatchmakingHandler) CreateMatchmakingRequestHandler(w http.ResponseWriter, r *http.Request) {
	var request dto.CreateMatchmakingRequest

	err := json.NewDecoder(r.Body).Decode(&request)
	if err != nil {
		response.WriteError(w, http.StatusBadRequest, "INVALID_JSON", "Request body contains invalid JSON", nil)
		return
	}

	matchmakingRequest, err := h.matchmakingService.CreateRequest(r.Context(), request)
	if err != nil {
		response.WriteAppError(w, err)
		return
	}

	response.WriteJSON(w, http.StatusCreated, toMatchmakingRequestResponse(matchmakingRequest))
}

// GetMatchmakingRequestHandler returns a matchmaking request by ID.
//
// @Summary Get matchmaking request
// @Description Returns a matchmaking request by its identifier.
// @Tags Matchmaking Requests
// @Produce json
// @Param request_id path string true "Matchmaking request ID"
// @Success 200 {object} dto.MatchmakingRequestResponse
// @Failure 404 {object} response.ErrorResponse
// @Failure 500 {object} response.ErrorResponse
// @Router /matchmaking/requests/{request_id} [get]
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

// GetPlayerMatchmakingRequestsHandler returns matchmaking requests created by a player.
//
// @Summary Get player matchmaking requests
// @Description Returns all matchmaking requests created by the specified player.
// @Tags Matchmaking Requests
// @Produce json
// @Param player_id path string true "Player ID"
// @Success 200 {array} dto.MatchmakingRequestResponse
// @Failure 500 {object} response.ErrorResponse
// @Router /players/{player_id}/matchmaking/requests [get]
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

// SearchCandidatesHandler searches suitable candidates for a matchmaking request.
//
// @Summary Search candidates
// @Description Retrieves players from the Python Player Service via gRPC, filters them, calculates scores and stores candidates.
// @Tags Candidates
// @Produce json
// @Param request_id path string true "Matchmaking request ID"
// @Success 200 {object} dto.SearchCandidatesResponse
// @Failure 400 {object} response.ErrorResponse
// @Failure 409 {object} response.ErrorResponse
// @Failure 500 {object} response.ErrorResponse
// @Router /matchmaking/requests/{request_id}/search [post]
func (h *MatchmakingHandler) SearchCandidatesHandler(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "request_id")
	if requestID == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "request_id is required", map[string]any{
			"field": "request_id",
		})
		return
	}

	candidates, err := h.matchmakingService.SearchCandidates(r.Context(), requestID)
	if err != nil {
		response.WriteAppError(w, err)
		return
	}

	candidateResponses := make([]dto.CandidateResponse, 0, len(candidates))
	for _, candidate := range candidates {
		candidateResponses = append(candidateResponses, toCandidateResponse(candidate))
	}

	response.WriteJSON(w, http.StatusOK, dto.SearchCandidatesResponse{
		RequestID:  requestID,
		Candidates: candidateResponses,
	})
}

// GetCandidatesHandler returns stored candidates for a matchmaking request.
//
// @Summary Get candidates
// @Description Returns candidates previously found and stored for the specified matchmaking request.
// @Tags Candidates
// @Produce json
// @Param request_id path string true "Matchmaking request ID"
// @Success 200 {object} dto.SearchCandidatesResponse
// @Failure 404 {object} response.ErrorResponse
// @Failure 500 {object} response.ErrorResponse
// @Router /matchmaking/requests/{request_id}/candidates [get]
func (h *MatchmakingHandler) GetCandidatesHandler(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "request_id")
	if requestID == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "request_id is required", map[string]any{
			"field": "request_id",
		})
		return
	}

	candidates, err := h.matchmakingService.GetCandidatesByRequestID(r.Context(), requestID)
	if err != nil {
		response.WriteError(w, http.StatusNotFound, "MATCHMAKING_REQUEST_NOT_FOUND", "Matchmaking request not found", map[string]any{
			"request_id": requestID,
		})
		return
	}

	candidateResponses := make([]dto.CandidateResponse, 0, len(candidates))
	for _, candidate := range candidates {
		candidateResponses = append(candidateResponses, toCandidateResponse(candidate))
	}

	response.WriteJSON(w, http.StatusOK, dto.SearchCandidatesResponse{
		RequestID:  requestID,
		Candidates: candidateResponses,
	})
}

// CreateMatchGroupHandler creates a match group from selected candidates.
//
// @Summary Create match group
// @Description Creates a match group using the request author and selected candidate IDs.
// @Tags Match Groups
// @Accept json
// @Produce json
// @Param request_id path string true "Matchmaking request ID"
// @Param request body dto.CreateMatchGroupRequest true "Selected candidate IDs"
// @Success 201 {object} dto.MatchGroupResponse
// @Failure 400 {object} response.ErrorResponse
// @Failure 409 {object} response.ErrorResponse
// @Failure 500 {object} response.ErrorResponse
// @Router /matchmaking/requests/{request_id}/group [post]
func (h *MatchmakingHandler) CreateMatchGroupHandler(w http.ResponseWriter, r *http.Request) {
	requestID := chi.URLParam(r, "request_id")
	if requestID == "" {
		response.WriteError(w, http.StatusBadRequest, "VALIDATION_ERROR", "request_id is required", map[string]any{
			"field": "request_id",
		})
		return
	}

	var request dto.CreateMatchGroupRequest

	err := json.NewDecoder(r.Body).Decode(&request)
	if err != nil {
		response.WriteError(w, http.StatusBadRequest, "INVALID_JSON", "Request body contains invalid JSON", nil)
		return
	}

	group, err := h.matchmakingService.CreateGroup(r.Context(), requestID, request.SelectedCandidateIDs)
	if err != nil {
		response.WriteAppError(w, err)
		return
	}

	response.WriteJSON(w, http.StatusCreated, toMatchGroupResponse(group))
}

func toMatchGroupResponse(group domain.MatchGroup) dto.MatchGroupResponse {
	return dto.MatchGroupResponse{
		ID:        group.ID,
		RequestID: group.RequestID,
		Members:   group.Members,
		Status:    group.Status,
		CreatedAt: group.CreatedAt.Format(time.RFC3339),
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

func toCandidateResponse(candidate domain.Candidate) dto.CandidateResponse {
	return dto.CandidateResponse{
		PlayerID:       candidate.PlayerID,
		Nickname:       candidate.Nickname,
		RiotID:         candidate.RiotID,
		CurrentRank:    candidate.CurrentRank,
		Region:         candidate.Region,
		MainRoles:      candidate.MainRoles,
		Status:         candidate.Status,
		TeammateRating: candidate.TeammateRating,
		Score:          candidate.Score,
	}
}
