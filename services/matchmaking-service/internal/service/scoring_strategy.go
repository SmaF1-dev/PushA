package service

import (
	"math"
	"pusha/matchmaking-service/internal/domain"
)

// ScoringStrategy defines how a candidate score is calculated.
//
// Different implementations use different weights for rank, rating, role match
// and status, which allows changing matchmaking behavior without changing the
// main search flow.
type ScoringStrategy interface {
	CalculateScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64
}

type BalancedScoringStrategy struct{}

func (s BalancedScoringStrategy) CalculateScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64 {
	rankScore := calculateRankScore(request, candidate)
	ratingScore := calculateRatingScore(candidate)
	roleScore := calculateRoleScore(request, candidate)
	statusScore := calculateStatusScore(candidate)

	return roundScore(
		rankScore*0.35 + ratingScore*0.3 + roleScore*0.2 + statusScore*0.15,
	)
}

type RankFocusedScoringStrategy struct{}

func (s RankFocusedScoringStrategy) CalculateScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64 {
	rankScore := calculateRankScore(request, candidate)
	ratingScore := calculateRatingScore(candidate)
	roleScore := calculateRoleScore(request, candidate)
	statusScore := calculateStatusScore(candidate)

	return roundScore(
		rankScore*0.55 +
			ratingScore*0.20 +
			roleScore*0.15 +
			statusScore*0.10,
	)
}

type RatingFocusedScoringStrategy struct{}

func (s RatingFocusedScoringStrategy) CalculateScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64 {
	rankScore := calculateRankScore(request, candidate)
	ratingScore := calculateRatingScore(candidate)
	roleScore := calculateRoleScore(request, candidate)
	statusScore := calculateStatusScore(candidate)

	return roundScore(
		rankScore*0.20 +
			ratingScore*0.55 +
			roleScore*0.15 +
			statusScore*0.10,
	)
}

type RoleFocusedScoringStrategy struct{}

func (s RoleFocusedScoringStrategy) CalculateScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64 {
	rankScore := calculateRankScore(request, candidate)
	ratingScore := calculateRatingScore(candidate)
	roleScore := calculateRoleScore(request, candidate)
	statusScore := calculateStatusScore(candidate)

	return roundScore(
		rankScore*0.20 +
			ratingScore*0.20 +
			roleScore*0.50 +
			statusScore*0.10,
	)
}

func NewScoringStrategy(strategy string) ScoringStrategy {
	switch strategy {
	case "RANK_FOCUSED":
		return RankFocusedScoringStrategy{}
	case "RATING_FOCUSED":
		return RatingFocusedScoringStrategy{}
	case "ROLE_FOCUSED":
		return RoleFocusedScoringStrategy{}
	case "BALANCED":
		return BalancedScoringStrategy{}
	default:
		return BalancedScoringStrategy{}
	}
}

func calculateRankScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64 {
	if !domain.IsValidValorantRank(candidate.CurrentRank) {
		return 0
	}

	if !domain.IsRankInRange(candidate.CurrentRank, request.MinRank, request.MaxRank) {
		return 0
	}

	return 100
}

func calculateRatingScore(candidate domain.Candidate) float64 {
	if candidate.TeammateRating <= 0 {
		return 0
	}

	if candidate.TeammateRating >= 5 {
		return 100
	}

	return candidate.TeammateRating / 5 * 100
}

func calculateRoleScore(request domain.MatchmakingRequest, candidate domain.Candidate) float64 {
	if len(request.RequiredRoles) == 0 {
		return 100
	}

	for _, requiredRole := range request.RequiredRoles {
		for _, candidateRole := range candidate.MainRoles {
			if requiredRole == candidateRole {
				return 100
			}
		}
	}

	return 40
}

func calculateStatusScore(candidate domain.Candidate) float64 {
	switch candidate.Status {
	case "READY_TO_PLAY":
		return 100
	case "ONLINE":
		return 70
	case "BUSY":
		return 30
	case "IN_GAME":
		return 20
	case "OFFLINE":
		return 0
	default:
		return 0
	}
}

func roundScore(score float64) float64 {
	return math.Round(score*10) / 10
}
