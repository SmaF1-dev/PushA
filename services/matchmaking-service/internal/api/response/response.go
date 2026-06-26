package response

import (
	"encoding/json"
	"errors"
	"net/http"
	"pusha/matchmaking-service/internal/apperror"
)

type ErrorResponse struct {
	Error ErrorBody `json:"error"`
}

type ErrorBody struct {
	Code    string         `json:"code"`
	Message string         `json:"message"`
	Details map[string]any `json:"details,omitempty"`
}

func WriteJSON(w http.ResponseWriter, statusCode int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	err := json.NewEncoder(w).Encode(data)
	if err != nil {
		http.Error(w, "failed to encode response", http.StatusInternalServerError)
	}
}

func WriteAppError(w http.ResponseWriter, err error) {
	var appErr *apperror.AppError

	if errors.As(err, &appErr) {
		status := http.StatusInternalServerError

		switch appErr.Type {
		case apperror.TypeValidation:
			status = http.StatusBadRequest
		case apperror.TypeConflict:
			status = http.StatusConflict
		case apperror.TypeNotFound:
			status = http.StatusNotFound
		case apperror.TypeInternal:
			status = http.StatusInternalServerError
		}

		var details map[string]any
		if appErr.Field != "" {
			details = map[string]any{
				"field": appErr.Field,
			}
		}

		WriteError(w, status, appErr.Code, appErr.Message, details)
		return
	}

	WriteError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Internal server error", nil)
}

func WriteError(w http.ResponseWriter, statusCode int, code string, message string, details map[string]any) {
	WriteJSON(w, statusCode, ErrorResponse{
		Error: ErrorBody{
			Code:    code,
			Message: message,
			Details: details,
		},
	})
}
