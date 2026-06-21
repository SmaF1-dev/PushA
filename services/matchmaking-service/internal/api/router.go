package api

import (
	"net/http"
	"pusha/matchmaking-service/internal/api/handlers"

	"github.com/go-chi/chi/v5"
)

func NewRouter() http.Handler {
	router := chi.NewRouter()

	router.Get("/health", handlers.HealthHandler)

	router.Route("/api/v1", func(r chi.Router) {
		r.Post("/matchmaking/requests", handlers.CreateMatchmakingRequestHandler)
	})

	return router
}
