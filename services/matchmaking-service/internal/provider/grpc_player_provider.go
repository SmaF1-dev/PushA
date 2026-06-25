package provider

import (
	"context"
	"fmt"
	"pusha/matchmaking-service/internal/domain"
	playerpb "pusha/matchmaking-service/pkg/proto"

	"github.com/google/uuid"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type GrpcPlayerProvider struct {
	conn   *grpc.ClientConn
	client playerpb.ValorantPlayerServiceClient
}

func NewGrpcPlayerProvider(address string) (*GrpcPlayerProvider, error) {
	conn, err := grpc.NewClient(
		address,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		return nil, fmt.Errorf("create player service grpc client: %w", err)
	}

	client := playerpb.NewValorantPlayerServiceClient(conn)

	return &GrpcPlayerProvider{
		conn:   conn,
		client: client,
	}, nil
}

func (p *GrpcPlayerProvider) Close() error {
	return p.conn.Close()
}

func (p *GrpcPlayerProvider) FindPlayers(ctx context.Context, request FindPlayersRequest) ([]domain.Candidate, error) {
	response, err := p.client.FindValorantPlayers(ctx, &playerpb.FindValorantPlayersRequest{
		ExcludedPlayerId:     request.ExcludedPlayerID,
		MinRank:              request.MinRank,
		MaxRank:              request.MaxRank,
		RequiredPlayerStatus: request.RequiredPlayerStatus,
		MinTeammateRating:    request.MinTeammateRating,
		Region:               request.Region,
		RequiredRoles:        request.RequiredRoles,
		Limit:                int32(request.Limit),
	})
	if err != nil {
		return nil, fmt.Errorf("find valorant players via grpc: %w", err)
	}

	candidates := make([]domain.Candidate, 0, len(response.GetCandidates()))

	for _, grpcCandidate := range response.GetCandidates() {
		candidates = append(candidates, domain.Candidate{
			ID:             uuid.NewString(),
			PlayerID:       grpcCandidate.GetPlayerId(),
			Nickname:       grpcCandidate.GetNickname(),
			RiotID:         grpcCandidate.GetRiotId(),
			CurrentRank:    grpcCandidate.GetCurrentRank(),
			Region:         grpcCandidate.GetRegion(),
			MainRoles:      grpcCandidate.GetMainRoles(),
			Status:         grpcCandidate.GetStatus(),
			TeammateRating: grpcCandidate.GetTeammateRating(),
		})
	}

	return candidates, nil
}
