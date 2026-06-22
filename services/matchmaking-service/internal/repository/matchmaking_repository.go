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

func (r *MatchmakingRepository) GetByID(ctx context.Context, id string) (domain.MatchmakingRequest, error) {
	query := `
		SELECT
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
		FROM matchmaking_requests
		WHERE id = $1
	`

	var request domain.MatchmakingRequest

	err := r.db.QueryRow(ctx, query, id).Scan(
		&request.ID,
		&request.AuthorID,
		&request.MinRank,
		&request.MaxRank,
		&request.RequiredPlayerStatus,
		&request.MinTeammateRating,
		&request.Region,
		&request.RequiredRoles,
		&request.NeededPlayers,
		&request.Strategy,
		&request.Status,
		&request.CreatedAt,
		&request.ExpiresAt,
	)
	if err != nil {
		return domain.MatchmakingRequest{}, err
	}

	return request, nil
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

func (r *MatchmakingRepository) GetByAuthorID(ctx context.Context, authorID string) ([]domain.MatchmakingRequest, error) {
	query := `
		SELECT
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
		FROM matchmaking_requests
		WHERE author_id = $1
		ORDER BY created_at DESC
	`

	rows, err := r.db.Query(ctx, query, authorID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var requests []domain.MatchmakingRequest

	for rows.Next() {
		var request domain.MatchmakingRequest

		err := rows.Scan(
			&request.ID,
			&request.AuthorID,
			&request.MinRank,
			&request.MaxRank,
			&request.RequiredPlayerStatus,
			&request.MinTeammateRating,
			&request.Region,
			&request.RequiredRoles,
			&request.NeededPlayers,
			&request.Strategy,
			&request.Status,
			&request.CreatedAt,
			&request.ExpiresAt,
		)
		if err != nil {
			return nil, err
		}

		requests = append(requests, request)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return requests, nil
}

func (r *MatchmakingRepository) HasActiveRequest(ctx context.Context, authorID string) (bool, error) {
	query := `
		SELECT EXISTS (
			SELECT 1
			FROM matchmaking_requests
			WHERE author_id = $1
			  AND status IN ('OPEN', 'SEARCHING')
		)
	`

	var exists bool

	err := r.db.QueryRow(ctx, query, authorID).Scan(&exists)
	if err != nil {
		return false, err
	}

	return exists, nil
}
