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
)

type MatchmakingService struct {
	matchmakingRepository *repository.MatchmakingRepository
}

func NewMatchmakingService(matchmakingRepository *repository.MatchmakingRepository) *MatchmakingService {
	return &MatchmakingService{
		matchmakingRepository: matchmakingRepository,
	}
}

func (s *MatchmakingService) CreateRequest(ctx context.Context, request dto.CreateMatchmakingRequest) (domain.MatchmakingRequest, error) {
	if err := validateCreateMatchmakingRequest(request); err != nil {
		return domain.MatchmakingRequest{}, err
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

	err := s.matchmakingRepository.Create(ctx, matchmakingRequest)
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

func validateCreateMatchmakingRequest(request dto.CreateMatchmakingRequest) error {
	if request.AuthorID == "" {
		return ErrAuthorIDRequired
	}

	if request.MinRank == "" {
		return ErrMinRankRequired
	}

	if request.MaxRank == "" {
		return ErrMaxRankRequired
	}

	if request.RequiredPlayerStatus == "" {
		return ErrRequiredPlayerStatusRequired
	}

	if request.MinTeammateRating < 0 || request.MinTeammateRating > 5 {
		return ErrInvalidMinTeammateRating
	}

	if request.Region == "" {
		return ErrRegionRequired
	}

	if request.NeededPlayers < 1 || request.NeededPlayers > 4 {
		return ErrInvalidNeededPlayers
	}

	if request.Strategy == "" {
		return ErrStrategyRequired
	}

	return nil
}
