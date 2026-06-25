package service

import "pusha/matchmaking-service/internal/domain"

// CandidateSpecification defines one eligibility rule for a matchmaking candidate.
type CandidateSpecification interface {
	IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool
}

type NotAuthorSpecification struct{}

func (s NotAuthorSpecification) IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	return candidate.PlayerID != request.AuthorID
}

type RankRangeSpecification struct{}

func (s RankRangeSpecification) IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	return domain.IsRankInRange(candidate.CurrentRank, request.MinRank, request.MaxRank)
}

type StatusSpecification struct{}

func (s StatusSpecification) IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	return candidate.Status == request.RequiredPlayerStatus
}

type MinRatingSpecification struct{}

func (s MinRatingSpecification) IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	return candidate.TeammateRating >= request.MinTeammateRating
}

type RegionSpecification struct{}

func (s RegionSpecification) IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	return candidate.Region == request.Region
}

type RoleSpecification struct{}

func (s RoleSpecification) IsSatisfiedBy(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	if len(request.RequiredRoles) == 0 {
		return true
	}

	for _, requiredRole := range request.RequiredRoles {
		for _, candidateRole := range candidate.MainRoles {
			if requiredRole == candidateRole {
				return true
			}
		}
	}

	return false
}

type CandidateFilter struct {
	specifications []CandidateSpecification
}

func NewCandidateFilter() CandidateFilter {
	return CandidateFilter{
		specifications: []CandidateSpecification{
			NotAuthorSpecification{},
			RankRangeSpecification{},
			StatusSpecification{},
			MinRatingSpecification{},
			RegionSpecification{},
			RoleSpecification{},
		},
	}
}

func (f CandidateFilter) Filter(request domain.MatchmakingRequest, candidates []domain.Candidate) []domain.Candidate {
	filteredCandidates := make([]domain.Candidate, 0, len(candidates))

	for _, candidate := range candidates {
		if f.isSatisfiedByAll(request, candidate) {
			filteredCandidates = append(filteredCandidates, candidate)
		}
	}

	return filteredCandidates
}

func (f CandidateFilter) isSatisfiedByAll(request domain.MatchmakingRequest, candidate domain.Candidate) bool {
	for _, specification := range f.specifications {
		if !specification.IsSatisfiedBy(request, candidate) {
			return false
		}
	}

	return true
}
