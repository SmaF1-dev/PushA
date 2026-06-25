package service

import (
	"errors"
	"testing"

	"pusha/matchmaking-service/internal/dto"
)

func TestValidateCreateMatchmakingRequest_ValidRequest(t *testing.T) {
	request := dto.CreateMatchmakingRequest{
		AuthorID:             "player_1",
		MinRank:              "GOLD_1",
		MaxRank:              "PLATINUM_3",
		RequiredPlayerStatus: "READY_TO_PLAY",
		MinTeammateRating:    4.0,
		Region:               "EU",
		RequiredRoles:        []string{"CONTROLLER", "SENTINEL"},
		NeededPlayers:        4,
		Strategy:             "BALANCED",
	}

	err := validateCreateMatchmakingRequest(request)
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
}

func TestValidateCreateMatchmakingRequest_AuthorIDRequired(t *testing.T) {
	request := dto.CreateMatchmakingRequest{
		MinRank:              "GOLD_1",
		MaxRank:              "PLATINUM_3",
		RequiredPlayerStatus: "READY_TO_PLAY",
		MinTeammateRating:    4.0,
		Region:               "EU",
		RequiredRoles:        []string{"CONTROLLER"},
		NeededPlayers:        4,
		Strategy:             "BALANCED",
	}

	err := validateCreateMatchmakingRequest(request)

	if !errors.Is(err, ErrAuthorIDRequired) {
		t.Fatalf("expected ErrAuthorIDRequired, got %v", err)
	}
}

func TestValidateCreateMatchmakingRequest_InvalidRankRange(t *testing.T) {
	request := dto.CreateMatchmakingRequest{
		AuthorID:             "player_1",
		MinRank:              "PLATINUM_3",
		MaxRank:              "GOLD_1",
		RequiredPlayerStatus: "READY_TO_PLAY",
		MinTeammateRating:    4.0,
		Region:               "EU",
		RequiredRoles:        []string{"CONTROLLER"},
		NeededPlayers:        4,
		Strategy:             "BALANCED",
	}

	err := validateCreateMatchmakingRequest(request)

	if !errors.Is(err, ErrInvalidRankRange) {
		t.Fatalf("expected ErrInvalidRankRange, got %v", err)
	}
}

func TestValidateCreateMatchmakingRequest_InvalidCases(t *testing.T) {
	validRequest := dto.CreateMatchmakingRequest{
		AuthorID:             "player_1",
		MinRank:              "GOLD_1",
		MaxRank:              "PLATINUM_3",
		RequiredPlayerStatus: "READY_TO_PLAY",
		MinTeammateRating:    4.0,
		Region:               "EU",
		RequiredRoles:        []string{"CONTROLLER"},
		NeededPlayers:        4,
		Strategy:             "BALANCED",
	}

	tests := []struct {
		name        string
		modify      func(request *dto.CreateMatchmakingRequest)
		expectedErr error
	}{
		{
			name: "missing author id",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.AuthorID = ""
			},
			expectedErr: ErrAuthorIDRequired,
		},
		{
			name: "missing min rank",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MinRank = ""
			},
			expectedErr: ErrMinRankRequired,
		},
		{
			name: "invalid min rank",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MinRank = "WOOD_1"
			},
			expectedErr: ErrInvalidMinRank,
		},
		{
			name: "missing max rank",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MaxRank = ""
			},
			expectedErr: ErrMaxRankRequired,
		},
		{
			name: "invalid max rank",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MaxRank = "MASTER_1"
			},
			expectedErr: ErrInvalidMaxRank,
		},
		{
			name: "invalid rank range",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MinRank = "PLATINUM_3"
				request.MaxRank = "GOLD_1"
			},
			expectedErr: ErrInvalidRankRange,
		},
		{
			name: "missing required player status",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.RequiredPlayerStatus = ""
			},
			expectedErr: ErrRequiredPlayerStatusRequired,
		},
		{
			name: "invalid required player status",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.RequiredPlayerStatus = "SLEEPING"
			},
			expectedErr: ErrInvalidRequiredPlayerStatus,
		},
		{
			name: "negative min teammate rating",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MinTeammateRating = -1
			},
			expectedErr: ErrInvalidMinTeammateRating,
		},
		{
			name: "too large min teammate rating",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.MinTeammateRating = 6
			},
			expectedErr: ErrInvalidMinTeammateRating,
		},
		{
			name: "missing region",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.Region = ""
			},
			expectedErr: ErrRegionRequired,
		},
		{
			name: "invalid required role",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.RequiredRoles = []string{"SNIPER"}
			},
			expectedErr: ErrInvalidRequiredRole,
		},
		{
			name: "needed players less than one",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.NeededPlayers = 0
			},
			expectedErr: ErrInvalidNeededPlayers,
		},
		{
			name: "needed players greater than four",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.NeededPlayers = 5
			},
			expectedErr: ErrInvalidNeededPlayers,
		},
		{
			name: "missing strategy",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.Strategy = ""
			},
			expectedErr: ErrStrategyRequired,
		},
		{
			name: "invalid strategy",
			modify: func(request *dto.CreateMatchmakingRequest) {
				request.Strategy = "RANDOM"
			},
			expectedErr: ErrInvalidStrategy,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			request := validRequest
			tt.modify(&request)

			err := validateCreateMatchmakingRequest(request)

			if !errors.Is(err, tt.expectedErr) {
				t.Fatalf("expected %v, got %v", tt.expectedErr, err)
			}
		})
	}
}
