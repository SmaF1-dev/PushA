package handlers

import (
	"net/http"
	"pusha/matchmaking-service/internal/api/response"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Service string `json:"service"`
}

func HealthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		response.WriteError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "Only GET method is allowed", nil)
		return
	}

	response.WriteJSON(w, http.StatusOK, HealthResponse{
		Status:  "ok",
		Service: "matchmaking-service",
	})
}
