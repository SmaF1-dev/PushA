package service

import (
	"context"
	"pusha/matchmaking-service/internal/apperror"
	"pusha/matchmaking-service/internal/domain"
	"pusha/matchmaking-service/internal/dto"
	"pusha/matchmaking-service/internal/provider"
	"pusha/matchmaking-service/internal/repository"
	"time"

	"github.com/google/uuid"
)

var (
	ErrAuthorIDRequired = apperror.NewValidation(
		"AUTHOR_ID_REQUIRED",
		"author_id is required",
		"author_id",
	)
	ErrMinRankRequired = apperror.NewValidation(
		"MIN_RANK_REQUIRED",
		"min_rank is required",
		"min_rank",
	)
	ErrMaxRankRequired = apperror.NewValidation(
		"MAX_RANK_REQUIRED",
		"max_rank is required",
		"max_rank",
	)
	ErrRequiredPlayerStatusRequired = apperror.NewValidation(
		"REQUIRED_PLAYER_STATUS_REQUIRED",
		"required_player_status is required",
		"required_player_status",
	)
	ErrInvalidMinTeammateRating = apperror.NewValidation(
		"INVALID_MIN_TEAMMATE_RATING",
		"min_teammate_rating must be between 0 and 5",
		"min_teammate_rating",
	)
	ErrRegionRequired = apperror.NewValidation(
		"REGION_REQUIRED",
		"region is required",
		"region",
	)
	ErrInvalidNeededPlayers = apperror.NewValidation(
		"INVALID_NEEDED_PLAYERS",
		"needed_players must be between 1 and 4",
		"needed_players",
	)
	ErrStrategyRequired = apperror.NewValidation(
		"STRATEGY_REQUIRED",
		"strategy is required",
		"strategy",
	)

	ErrInvalidMinRank = apperror.NewValidation(
		"INVALID_MIN_RANK",
		"min_rank is invalid",
		"min_rank",
	)
	ErrInvalidMaxRank = apperror.NewValidation(
		"INVALID_MAX_RANK",
		"max_rank is invalid",
		"max_rank",
	)
	ErrInvalidRankRange = apperror.NewValidation(
		"INVALID_RANK_RANGE",
		"min_rank must be less than or equal to max_rank",
		"min_rank",
	)
	ErrInvalidRequiredPlayerStatus = apperror.NewValidation(
		"INVALID_REQUIRED_PLAYER_STATUS",
		"required_player_status is invalid",
		"required_player_status",
	)
	ErrInvalidRequiredRole = apperror.NewValidation(
		"INVALID_REQUIRED_ROLE",
		"required_roles contains invalid role",
		"required_roles",
	)
	ErrInvalidStrategy = apperror.NewValidation(
		"INVALID_STRATEGY",
		"strategy is invalid",
		"strategy",
	)

	ErrActiveRequestAlreadyExists = apperror.NewConflict(
		"ACTIVE_REQUEST_ALREADY_EXISTS",
		"active matchmaking request already exists",
	)
	ErrRequestIsNotOpen = apperror.NewConflict(
		"REQUEST_IS_NOT_OPEN",
		"matchmaking request is not open",
	)
	ErrRequestIsNotSearching = apperror.NewConflict(
		"REQUEST_IS_NOT_SEARCHING",
		"matchmaking request is not searching",
	)
	ErrSelectedCandidatesRequired = apperror.NewValidation(
		"SELECTED_CANDIDATES_REQUIRED",
		"selected_candidate_ids is required",
		"selected_candidate_ids",
	)
	ErrTooManySelectedCandidates = apperror.NewValidation(
		"TOO_MANY_SELECTED_CANDIDATES",
		"too many selected candidates",
		"selected_candidate_ids",
	)
	ErrSelectedCandidateNotFound = apperror.NewValidation(
		"SELECTED_CANDIDATE_NOT_FOUND",
		"selected candidate not found",
		"selected_candidate_ids",
	)
)

// MatchmakingService contains the main business logic of the Go matchmaking service.
//
// It creates matchmaking requests, retrieves candidates from PlayerProvider,
// filters and scores them, stores candidates, and creates match groups.
type MatchmakingService struct {
	matchmakingRepository *repository.MatchmakingRepository
	candidateRepository   *repository.CandidateRepository
	groupRepository       *repository.GroupRepository
	playerProvider        provider.PlayerProvider
}

func NewMatchmakingService(
	matchmakingRepository *repository.MatchmakingRepository,
	candidateRepository *repository.CandidateRepository,
	groupRepository *repository.GroupRepository,
	playerProvider provider.PlayerProvider,
) *MatchmakingService {
	return &MatchmakingService{
		matchmakingRepository: matchmakingRepository,
		candidateRepository:   candidateRepository,
		groupRepository:       groupRepository,
		playerProvider:        playerProvider,
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

// SearchCandidates retrieves candidates from the configured PlayerProvider,
// filters them using Specification Pattern, calculates score using Strategy
// Pattern, stores candidates and moves the request to SEARCHING status.
func (s *MatchmakingService) SearchCandidates(ctx context.Context, requestID string) ([]domain.Candidate, error) {
	matchmakingRequest, err := s.matchmakingRepository.GetByID(ctx, requestID)
	if err != nil {
		return nil, err
	}

	if matchmakingRequest.Status != domain.MatchmakingRequestStatusOpen {
		return nil, ErrRequestIsNotOpen
	}

	candidates, err := s.playerProvider.FindPlayers(ctx, provider.FindPlayersRequest{
		ExcludedPlayerID:     matchmakingRequest.AuthorID,
		MinRank:              matchmakingRequest.MinRank,
		MaxRank:              matchmakingRequest.MaxRank,
		RequiredPlayerStatus: matchmakingRequest.RequiredPlayerStatus,
		MinTeammateRating:    matchmakingRequest.MinTeammateRating,
		Region:               matchmakingRequest.Region,
		RequiredRoles:        matchmakingRequest.RequiredRoles,
		Limit:                matchmakingRequest.NeededPlayers * 3,
	})

	if err != nil {
		return nil, err
	}

	for i := range candidates {
		candidates[i].RequestID = requestID
	}

	candidateFilter := NewCandidateFilter()
	candidates = candidateFilter.Filter(matchmakingRequest, candidates)

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

// CreateGroup creates a match group from selected candidates and the request author.
// The request must already be in SEARCHING status.
func (s *MatchmakingService) CreateGroup(ctx context.Context, requestID string, selectedCandidateIDs []string) (domain.MatchGroup, error) {
	if len(selectedCandidateIDs) == 0 {
		return domain.MatchGroup{}, ErrSelectedCandidatesRequired
	}

	matchmakingRequest, err := s.matchmakingRepository.GetByID(ctx, requestID)
	if err != nil {
		return domain.MatchGroup{}, err
	}

	if matchmakingRequest.Status != domain.MatchmakingRequestStatusSearching {
		return domain.MatchGroup{}, ErrRequestIsNotSearching
	}

	if len(selectedCandidateIDs) > matchmakingRequest.NeededPlayers {
		return domain.MatchGroup{}, ErrTooManySelectedCandidates
	}

	candidates, err := s.candidateRepository.GetByRequestID(ctx, requestID)
	if err != nil {
		return domain.MatchGroup{}, err
	}

	candidateByPlayerID := make(map[string]domain.Candidate)
	for _, candidate := range candidates {
		candidateByPlayerID[candidate.PlayerID] = candidate
	}

	for _, selectedCandidateID := range selectedCandidateIDs {
		if _, ok := candidateByPlayerID[selectedCandidateID]; !ok {
			return domain.MatchGroup{}, ErrSelectedCandidateNotFound
		}
	}

	members := make([]string, 0, len(selectedCandidateIDs)+1)
	members = append(members, matchmakingRequest.AuthorID)
	members = append(members, selectedCandidateIDs...)

	group := domain.MatchGroup{
		ID:        uuid.NewString(),
		RequestID: requestID,
		Members:   members,
		Status:    domain.MatchGroupStatusCreated,
		CreatedAt: time.Now().UTC(),
	}

	err = s.groupRepository.Create(ctx, group)
	if err != nil {
		return domain.MatchGroup{}, err
	}

	err = s.matchmakingRepository.UpdateStatus(ctx, requestID, domain.MatchmakingRequestStatusCompleted)
	if err != nil {
		return domain.MatchGroup{}, err
	}

	return group, nil
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
