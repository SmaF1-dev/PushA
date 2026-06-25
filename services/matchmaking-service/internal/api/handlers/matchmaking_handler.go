package handlers

import (
	"context"
	"encoding/json"
	"log"
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
		log.Printf("search candidates error: %v", err)
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
