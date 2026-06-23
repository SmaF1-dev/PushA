package service

import (
	"context"
	"errors"
	"pusha/matchmaking-service/internal/domain"
	"pusha/matchmaking-service/internal/dto"
	"pusha/matchmaking-service/internal/repository"
	"time"

	"github.com/google/uuid"
)

var (
	ErrAuthorIDRequired             = errors.New("author_id is required")
	ErrMinRankRequired              = errors.New("min_rank is required")
	ErrMaxRankRequired              = errors.New("max_rank is required")
	ErrRequiredPlayerStatusRequired = errors.New("required_player_status is required")
	ErrInvalidMinTeammateRating     = errors.New("min_teammate_rating must be between 0 and 5")
	ErrRegionRequired               = errors.New("region is required")
	ErrInvalidNeededPlayers         = errors.New("needed_players must be between 1 and 4")
	ErrStrategyRequired             = errors.New("strategy is required")

	ErrInvalidMinRank              = errors.New("min_rank is invalid")
	ErrInvalidMaxRank              = errors.New("max_rank is invalid")
	ErrInvalidRankRange            = errors.New("min_rank must be less than or equal to max_rank")
	ErrInvalidRequiredPlayerStatus = errors.New("required_player_status is invalid")
	ErrInvalidRequiredRole         = errors.New("required_roles contains invalid role")
	ErrInvalidStrategy             = errors.New("strategy is invalid")

	ErrActiveRequestAlreadyExists = errors.New("active matchmaking request already exists")
	ErrRequestIsNotOpen           = errors.New("matchmaking request is not open")
)

type MatchmakingService struct {
	matchmakingRepository *repository.MatchmakingRepository
	candidateRepository   *repository.CandidateRepository
}

func NewMatchmakingService(
	matchmakingRepository *repository.MatchmakingRepository,
	candidateRepository *repository.CandidateRepository,
) *MatchmakingService {
	return &MatchmakingService{
		matchmakingRepository: matchmakingRepository,
		candidateRepository:   candidateRepository,
	}
}

func (s *MatchmakingService) CreateRequest(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error) {
	if err := validateCreateMatchmakingRequest(request); err != nil {
		return domain.MatchmakingRequest{}, err
	}

	hasActiveRequest, err := s.matchmakingRepository.HasActiveRequest(ctx, request.AuthorID)
	if err != nil {
		return domain.MatchmakingRequest{}, err
	}

	if hasActiveRequest {
		return domain.MatchmakingRequest{}, ErrActiveRequestAlreadyExists
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
		Status:               domain.MatchmakingRequestStatusOpen,
		CreatedAt:            now,
		ExpiresAt:            expiresAt,
	}

	err = s.matchmakingRepository.Create(ctx, matchmakingRequest)
	if err != nil {
		return domain.MatchmakingRequest{}, err
	}

	return matchmakingRequest, nil
}

func (s *MatchmakingService) GetRequestByID(ctx context.Context, requestID string) (domain.MatchmakingRequest, error) {
	return s.matchmakingRepository.GetByID(ctx, requestID)
}

func (s *MatchmakingService) GetRequestsByAuthorID(ctx context.Context, authorID string) ([]domain.MatchmakingRequest, error) {
	return s.matchmakingRepository.GetByAuthorID(ctx, authorID)
}

func (s *MatchmakingService) SearchCandidates(ctx context.Context, requestID string) ([]domain.Candidate, error) {
	matchmakingRequest, err := s.matchmakingRepository.GetByID(ctx, requestID)
	if err != nil {
		return nil, err
	}

	if matchmakingRequest.Status != domain.MatchmakingRequestStatusOpen {
		return nil, ErrRequestIsNotOpen
	}

	now := time.Now().UTC()

	candidates := []domain.Candidate{
		{
			ID:             uuid.NewString(),
			RequestID:      requestID,
			PlayerID:       "player_2",
			Nickname:       "SmokeMaster",
			RiotID:         "SmokeMaster#EUW",
			CurrentRank:    "GOLD_2",
			Region:         matchmakingRequest.Region,
			MainRoles:      []string{"CONTROLLER"},
			Status:         "READY_TO_PLAY",
			TeammateRating: 4.5,
			Score:          87.5,
			CreatedAt:      now,
		},
		{
			ID:             uuid.NewString(),
			RequestID:      requestID,
			PlayerID:       "player_3",
			Nickname:       "SentinelGuy",
			RiotID:         "SentinelGuy#EUW",
			CurrentRank:    "PLATINUM_1",
			Region:         matchmakingRequest.Region,
			MainRoles:      []string{"SENTINEL"},
			Status:         "READY_TO_PLAY",
			TeammateRating: 4.2,
			Score:          82.0,
			CreatedAt:      now,
		},
		{
			ID:             uuid.NewString(),
			RequestID:      requestID,
			PlayerID:       "player_4",
			Nickname:       "FlashBoy",
			RiotID:         "FlashBoy#EUW",
			CurrentRank:    "GOLD_3",
			Region:         matchmakingRequest.Region,
			MainRoles:      []string{"INITIATOR"},
			Status:         "READY_TO_PLAY",
			TeammateRating: 3.9,
			Score:          76.5,
			CreatedAt:      now,
		},
	}

	scoringStrategy := NewScoringStrategy(matchmakingRequest.Strategy)

	for i := range candidates {
		candidates[i].Score = scoringStrategy.CalculateScore(matchmakingRequest, candidates[i])
	}

	err = s.candidateRepository.SaveMany(ctx, candidates)
	if err != nil {
		return nil, err
	}

	err = s.matchmakingRepository.UpdateStatus(ctx, requestID, domain.MatchmakingRequestStatusSearching)
	if err != nil {
		return nil, err
	}

	return candidates, nil
}

func (s *MatchmakingService) GetCandidatesByRequestID(ctx context.Context, requestID string) ([]domain.Candidate, error) {
	_, err := s.matchmakingRepository.GetByID(ctx, requestID)
	if err != nil {
		return nil, err
	}

	return s.candidateRepository.GetByRequestID(ctx, requestID)
}

func validateCreateMatchmakingRequest(request dto.CreateMatchmakingRequest) error {
	if request.AuthorID == "" {
		return ErrAuthorIDRequired
	}

	if request.MinRank == "" {
		return ErrMinRankRequired
	}

	if !domain.IsValidValorantRank(request.MinRank) {
		return ErrInvalidMinRank
	}

	if request.MaxRank == "" {
		return ErrMaxRankRequired
	}

	if !domain.IsValidValorantRank(request.MaxRank) {
		return ErrInvalidMaxRank
	}

	if !domain.IsRankRangeValid(request.MinRank, request.MaxRank) {
		return ErrInvalidRankRange
	}

	if request.RequiredPlayerStatus == "" {
		return ErrRequiredPlayerStatusRequired
	}

	if !domain.IsValidPlayerStatus(request.RequiredPlayerStatus) {
		return ErrInvalidRequiredPlayerStatus
	}

	if request.MinTeammateRating < 0 || request.MinTeammateRating > 5 {
		return ErrInvalidMinTeammateRating
	}

	if request.Region == "" {
		return ErrRegionRequired
	}

	for _, role := range request.RequiredRoles {
		if !domain.IsValidValorantRole(role) {
			return ErrInvalidRequiredRole
		}
	}

	if request.NeededPlayers < 1 || request.NeededPlayers > 4 {
		return ErrInvalidNeededPlayers
	}

	if request.Strategy == "" {
		return ErrStrategyRequired
	}

	if !domain.IsValidMatchingStrategy(request.Strategy) {
		return ErrInvalidStrategy
	}

	return nil
}
