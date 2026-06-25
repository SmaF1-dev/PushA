package response

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"pusha/matchmaking-service/internal/apperror"
)

func TestWriteAppError_ValidationError(t *testing.T) {
	rec := httptest.NewRecorder()

	err := apperror.NewValidation(
		"AUTHOR_ID_REQUIRED",
		"author_id is required",
		"author_id",
	)

	WriteAppError(rec, err)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("expected status 400, got %d", rec.Code)
	}

	body := rec.Body.String()

	if !strings.Contains(body, `"code":"AUTHOR_ID_REQUIRED"`) {
		t.Fatalf("expected AUTHOR_ID_REQUIRED in response, got %s", body)
	}

	if !strings.Contains(body, `"field":"author_id"`) {
		t.Fatalf("expected field author_id in response, got %s", body)
	}
}

func TestWriteAppError_ConflictError(t *testing.T) {
	rec := httptest.NewRecorder()

	err := apperror.NewConflict(
		"ACTIVE_REQUEST_ALREADY_EXISTS",
		"active matchmaking request already exists",
	)

	WriteAppError(rec, err)

	if rec.Code != http.StatusConflict {
		t.Fatalf("expected status 409, got %d", rec.Code)
	}

	if !strings.Contains(rec.Body.String(), `"code":"ACTIVE_REQUEST_ALREADY_EXISTS"`) {
		t.Fatalf("expected ACTIVE_REQUEST_ALREADY_EXISTS in response, got %s", rec.Body.String())
	}
}

func TestWriteAppError_UnknownError(t *testing.T) {
	rec := httptest.NewRecorder()

	WriteAppError(rec, assertAnUnknownError{})

	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("expected status 500, got %d", rec.Code)
	}

	if !strings.Contains(rec.Body.String(), `"code":"INTERNAL_ERROR"`) {
		t.Fatalf("expected INTERNAL_ERROR in response, got %s", rec.Body.String())
	}
}

type assertAnUnknownError struct{}

func (e assertAnUnknownError) Error() string {
	return "unknown error"
}
