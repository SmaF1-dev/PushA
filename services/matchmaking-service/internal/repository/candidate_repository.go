package repository

import (
	"context"
	"pusha/matchmaking-service/internal/domain"

	"github.com/jackc/pgx/v5/pgxpool"
)

type CandidateRepository struct {
	db *pgxpool.Pool
}

func NewCandidateRepository(db *pgxpool.Pool) *CandidateRepository {
	return &CandidateRepository{
		db: db,
	}
}

func (r *CandidateRepository) SaveMany(ctx context.Context, candidates []domain.Candidate) error {
	query := `
		INSERT INTO candidates (
			id,
			request_id,
			player_id,
			nickname,
			riot_id,
			current_rank,
			region,
			main_roles,
			status,
			teammate_rating,
			score,
			created_at
		)
		VALUES (
			$1, $2, $3, $4, $5, $6,
			$7, $8, $9, $10, $11, $12
		)
	`

	for _, candidate := range candidates {
		_, err := r.db.Exec(
			ctx,
			query,
			candidate.ID,
			candidate.RequestID,
			candidate.PlayerID,
			candidate.Nickname,
			candidate.RiotID,
			candidate.CurrentRank,
			candidate.Region,
			candidate.MainRoles,
			candidate.Status,
			candidate.TeammateRating,
			candidate.Score,
			candidate.CreatedAt,
		)
		if err != nil {
			return err
		}
	}

	return nil
}

func (r *CandidateRepository) GetByRequestID(ctx context.Context, requestID string) ([]domain.Candidate, error) {
	query := `
		SELECT
			id,
			request_id,
			player_id,
			nickname,
			riot_id,
			current_rank,
			region,
			main_roles,
			status,
			teammate_rating,
			score,
			created_at
		FROM candidates
		WHERE request_id = $1
		ORDER BY score DESC
	`

	rows, err := r.db.Query(ctx, query, requestID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var candidates []domain.Candidate

	for rows.Next() {
		var candidate domain.Candidate
		err := rows.Scan(
			&candidate.ID,
			&candidate.RequestID,
			&candidate.PlayerID,
			&candidate.Nickname,
			&candidate.RiotID,
			&candidate.CurrentRank,
			&candidate.Region,
			&candidate.MainRoles,
			&candidate.Status,
			&candidate.TeammateRating,
			&candidate.Score,
			&candidate.CreatedAt,
		)

		if err != nil {
			return nil, err
		}

		candidates = append(candidates, candidate)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return candidates, nil
}
