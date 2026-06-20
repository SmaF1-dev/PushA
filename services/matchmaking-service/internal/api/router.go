package api

import (
	"net/http"
	"pusha/matchmaking-service/internal/api/handlers"
)

func NewRouter() http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", handlers.HealthHandler)

	return mux
}
