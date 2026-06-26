package repository

import (
	"context"
	"pusha/matchmaking-service/internal/domain"

	"github.com/jackc/pgx/v5/pgxpool"
)

// GroupRepository stores match groups and their members in PostgreSQL.
type GroupRepository struct {
	db *pgxpool.Pool
}

func NewGroupRepository(db *pgxpool.Pool) *GroupRepository {
	return &GroupRepository{
		db: db,
	}
}

// Create saves a match group and all its members in a single transaction.
// If any insert fails, the transaction is rolled back.
func (r *GroupRepository) Create(ctx context.Context, group domain.MatchGroup) error {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	groupQuery := `
		INSERT INTO match_groups (
			id,
			request_id,
			status,
			created_at
		)
		VALUES ($1, $2, $3, $4)
	`

	_, err = tx.Exec(
		ctx,
		groupQuery,
		group.ID,
		group.RequestID,
		group.Status,
		group.CreatedAt,
	)
	if err != nil {
		return err
	}

	memberQuery := `
		INSERT INTO match_group_members (
			group_id,
			player_id
		)
		VALUES ($1, $2)
	`

	for _, memberID := range group.Members {
		_, err := tx.Exec(ctx, memberQuery, group.ID, memberID)
		if err != nil {
			return err
		}
	}

	return tx.Commit(ctx)
}
