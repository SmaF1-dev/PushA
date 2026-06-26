package apperror

import "testing"

func TestNewValidation(t *testing.T) {
	err := NewValidation("AUTHOR_ID_REQUIRED", "author_id is required", "author_id")

	if err.Type != TypeValidation {
		t.Fatalf("expected type %s, got %s", TypeValidation, err.Type)
	}

	if err.Code != "AUTHOR_ID_REQUIRED" {
		t.Fatalf("expected code AUTHOR_ID_REQUIRED, got %s", err.Code)
	}

	if err.Message != "author_id is required" {
		t.Fatalf("unexpected message: %s", err.Message)
	}

	if err.Field != "author_id" {
		t.Fatalf("expected field author_id, got %s", err.Field)
	}

	if err.Error() != "author_id is required" {
		t.Fatalf("unexpected Error() result: %s", err.Error())
	}
}

func TestNewConflict(t *testing.T) {
	err := NewConflict("ACTIVE_REQUEST_ALREADY_EXISTS", "active matchmaking request already exists")

	if err.Type != TypeConflict {
		t.Fatalf("expected type %s, got %s", TypeConflict, err.Type)
	}

	if err.Field != "" {
		t.Fatalf("expected empty field, got %s", err.Field)
	}
}

func TestNewNotFound(t *testing.T) {
	err := NewNotFound("MATCHMAKING_REQUEST_NOT_FOUND", "matchmaking request not found")

	if err.Type != TypeNotFound {
		t.Fatalf("expected type %s, got %s", TypeNotFound, err.Type)
	}
}

func TestNewInternal(t *testing.T) {
	err := NewInternal("INTERNAL_ERROR", "internal error")

	if err.Type != TypeInternal {
		t.Fatalf("expected type %s, got %s", TypeInternal, err.Type)
	}
}
