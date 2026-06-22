package repository

import (
	"context"
	"pusha/matchmaking-service/internal/domain"

	"github.com/jackc/pgx/v5/pgxpool"
)

type MatchmakingRepository struct {
	db *pgxpool.Pool
}

func NewMatchmakingRepository(db *pgxpool.Pool) *MatchmakingRepository {
	return &MatchmakingRepository{
		db: db,
	}
}

func (r *MatchmakingRepository) Create(ctx context.Context, request domain.MatchmakingRequest) error {
	query := `
		INSERT INTO matchmaking_requests (
			id,
			author_id,
			min_rank,
			max_rank,
			required_player_status,
			min_teammate_rating,
			region,
			required_roles,
			needed_players,
			strategy,
			status,
			created_at,
			expires_at
		)
		VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8,
			$9, $10, $11, $12, $13
		)
	`

	_, err := r.db.Exec(
		ctx,
		query,
		request.ID,
		request.AuthorID,
		request.MinRank,
		request.MaxRank,
		request.RequiredPlayerStatus,
		request.MinTeammateRating,
		request.Region,
		request.RequiredRoles,
		request.NeededPlayers,
		request.Strategy,
		request.Status,
		request.CreatedAt,
		request.ExpiresAt,
	)

	return err
}
