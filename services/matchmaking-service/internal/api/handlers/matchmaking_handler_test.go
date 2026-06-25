package handlers

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/go-chi/chi/v5"

	"pusha/matchmaking-service/internal/apperror"
	"pusha/matchmaking-service/internal/domain"
	"pusha/matchmaking-service/internal/dto"
)

type fakeMatchmakingService struct {
	createRequestFunc          func(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error)
	getRequestByIDFunc         func(ctx context.Context, requestID string) (domain.MatchmakingRequest, error)
	getRequestsByAuthorIDFunc  func(ctx context.Context, authorID string) ([]domain.MatchmakingRequest, error)
	searchCandidatesFunc       func(ctx context.Context, requestID string) ([]domain.Candidate, error)
	getCandidatesByRequestFunc func(ctx context.Context, requestID string) ([]domain.Candidate, error)
	createGroupFunc            func(ctx context.Context, requestID string, selectedCandidateIDs []string) (domain.MatchGroup, error)
}

func (s fakeMatchmakingService) CreateRequest(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error) {
	return s.createRequestFunc(ctx, request)
}

func (s fakeMatchmakingService) GetRequestByID(ctx context.Context, requestID string) (domain.MatchmakingRequest, error) {
	return s.getRequestByIDFunc(ctx, requestID)
}

func (s fakeMatchmakingService) GetRequestsByAuthorID(ctx context.Context, authorID string) ([]domain.MatchmakingRequest, error) {
	return s.getRequestsByAuthorIDFunc(ctx, authorID)
}

func (s fakeMatchmakingService) SearchCandidates(ctx context.Context, requestID string) ([]domain.Candidate, error) {
	return s.searchCandidatesFunc(ctx, requestID)
}

func (s fakeMatchmakingService) GetCandidatesByRequestID(ctx context.Context, requestID string) ([]domain.Candidate, error) {
	return s.getCandidatesByRequestFunc(ctx, requestID)
}

func (s fakeMatchmakingService) CreateGroup(ctx context.Context, requestID string, selectedCandidateIDs []string) (domain.MatchGroup, error) {
	return s.createGroupFunc(ctx, requestID, selectedCandidateIDs)
}

func TestCreateMatchmakingRequestHandler_Success(t *testing.T) {
	now := time.Now().UTC()

	service := fakeMatchmakingService{
		createRequestFunc: func(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error) {
			if request.AuthorID != "player_1" {
				t.Fatalf("expected author_id player_1, got %s", request.AuthorID)
			}

			return domain.MatchmakingRequest{
				ID:                   "request_1",
				AuthorID:             request.AuthorID,
				MinRank:              request.MinRank,
				MaxRank:              request.MaxRank,
				RequiredPlayerStatus: request.RequiredPlayerStatus,
				MinTeammateRating:    request.MinTeammateRating,
				Region:               request.Region,
				RequiredRoles:        request.RequiredRoles,
				NeededPlayers:        request.NeededPlayers,
				Strategy:             request.Strategy,
				Status:               domain.MatchmakingRequestStatusOpen,
				CreatedAt:            now,
				ExpiresAt:            now.Add(time.Hour),
			}, nil
		},
	}

	handler := NewMatchmakingHandler(service)

	body := `{
		"author_id": "player_1",
		"min_rank": "GOLD_1",
		"max_rank": "PLATINUM_3",
		"required_player_status": "READY_TO_PLAY",
		"min_teammate_rating": 4.0,
		"region": "EU",
		"required_roles": ["CONTROLLER"],
		"needed_players": 4,
		"strategy": "BALANCED"
	}`

	req := httptest.NewRequest(http.MethodPost, "/api/v1/matchmaking/requests", strings.NewReader(body))
	rec := httptest.NewRecorder()

	handler.CreateMatchmakingRequestHandler(rec, req)

	if rec.Code != http.StatusCreated {
		t.Fatalf("expected status 201, got %d; body: %s", rec.Code, rec.Body.String())
	}

	if !strings.Contains(rec.Body.String(), `"id":"request_1"`) {
		t.Fatalf("expected response to contain request id, got %s", rec.Body.String())
	}
}

func TestCreateMatchmakingRequestHandler_ValidationError(t *testing.T) {
	service := fakeMatchmakingService{
		createRequestFunc: func(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error) {
			return domain.MatchmakingRequest{}, apperror.NewValidation(
				"AUTHOR_ID_REQUIRED",
				"author_id is required",
				"author_id",
			)
		},
	}

	handler := NewMatchmakingHandler(service)

	body := `{
		"min_rank": "GOLD_1",
		"max_rank": "PLATINUM_3",
		"required_player_status": "READY_TO_PLAY",
		"min_teammate_rating": 4.0,
		"region": "EU",
		"required_roles": ["CONTROLLER"],
		"needed_players": 4,
		"strategy": "BALANCED"
	}`

	req := httptest.NewRequest(http.MethodPost, "/api/v1/matchmaking/requests", strings.NewReader(body))
	rec := httptest.NewRecorder()

	handler.CreateMatchmakingRequestHandler(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("expected status 400, got %d; body: %s", rec.Code, rec.Body.String())
	}

	if !strings.Contains(rec.Body.String(), `"code":"AUTHOR_ID_REQUIRED"`) {
		t.Fatalf("expected AUTHOR_ID_REQUIRED, got %s", rec.Body.String())
	}
}

func TestSearchCandidatesHandler_Success(t *testing.T) {
	service := fakeMatchmakingService{
		searchCandidatesFunc: func(ctx context.Context, requestID string) ([]domain.Candidate, error) {
			if requestID != "request_1" {
				t.Fatalf("expected request_1, got %s", requestID)
			}

			return []domain.Candidate{
				{
					PlayerID:       "player_2",
					Nickname:       "SmokeMaster",
					RiotID:         "SmokeMaster#EUW",
					CurrentRank:    "GOLD_2",
					Region:         "EU",
					MainRoles:      []string{"CONTROLLER"},
					Status:         "READY_TO_PLAY",
					TeammateRating: 4.5,
					Score:          97,
				},
			}, nil
		},
	}

	handler := NewMatchmakingHandler(service)

	r := chi.NewRouter()
	r.Post("/api/v1/matchmaking/requests/{request_id}/search", handler.SearchCandidatesHandler)

	req := httptest.NewRequest(http.MethodPost, "/api/v1/matchmaking/requests/request_1/search", nil)
	rec := httptest.NewRecorder()

	r.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d; body: %s", rec.Code, rec.Body.String())
	}

	if !strings.Contains(rec.Body.String(), `"player_id":"player_2"`) {
		t.Fatalf("expected response to contain candidate player_2, got %s", rec.Body.String())
	}
}

func TestCreateMatchGroupHandler_Success(t *testing.T) {
	now := time.Now().UTC()

	service := fakeMatchmakingService{
		createGroupFunc: func(ctx context.Context, requestID string, selectedCandidateIDs []string) (domain.MatchGroup, error) {
			if requestID != "request_1" {
				t.Fatalf("expected request_1, got %s", requestID)
			}

			if len(selectedCandidateIDs) != 2 {
				t.Fatalf("expected 2 selected candidates, got %d", len(selectedCandidateIDs))
			}

			return domain.MatchGroup{
				ID:        "group_1",
				RequestID: requestID,
				Members:   []string{"player_1", "player_2", "player_3"},
				Status:    domain.MatchGroupStatusCreated,
				CreatedAt: now,
			}, nil
		},
	}

	handler := NewMatchmakingHandler(service)

	r := chi.NewRouter()
	r.Post("/api/v1/matchmaking/requests/{request_id}/group", handler.CreateMatchGroupHandler)

	body := `{
		"selected_candidate_ids": ["player_2", "player_3"]
	}`

	req := httptest.NewRequest(http.MethodPost, "/api/v1/matchmaking/requests/request_1/group", strings.NewReader(body))
	rec := httptest.NewRecorder()

	r.ServeHTTP(rec, req)

	if rec.Code != http.StatusCreated {
		t.Fatalf("expected status 201, got %d; body: %s", rec.Code, rec.Body.String())
	}

	if !strings.Contains(rec.Body.String(), `"id":"group_1"`) {
		t.Fatalf("expected group_1 in response, got %s", rec.Body.String())
	}
}
