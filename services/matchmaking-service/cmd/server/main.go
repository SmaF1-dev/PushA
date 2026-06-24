package main

import (
	"log"
	"net/http"
	"pusha/matchmaking-service/internal/api"
	"pusha/matchmaking-service/internal/api/handlers"
	"pusha/matchmaking-service/internal/config"
	"pusha/matchmaking-service/internal/db"
	"pusha/matchmaking-service/internal/provider"
	"pusha/matchmaking-service/internal/repository"
	"pusha/matchmaking-service/internal/service"
)

func main() {
	cfg := config.Load()

	postgresPool, err := db.NewPostgresPool(cfg.DatabaseURL)
	if err != nil {
		log.Fatal("failed to connect to PostgreSQL: ", err)
	}
	defer postgresPool.Close()

	matchmakingRepository := repository.NewMatchmakingRepository(postgresPool)
	candidateRepository := repository.NewCandidateRepository(postgresPool)
	playerProvider := provider.NewMockPlayerProvider()
	groupRepository := repository.NewGroupRepository(postgresPool)
	matchmakingService := service.NewMatchmakingService(
		matchmakingRepository,
		candidateRepository,
		groupRepository,
		playerProvider,
	)
	matchmakingHandler := handlers.NewMatchmakingHandler(matchmakingService)

	router := api.NewRouter(matchmakingHandler)

	addr := ":" + cfg.HTTPPort

	log.Println("Matchmaking service started on", addr)

	err = http.ListenAndServe(addr, router)
	if err != nil {
		log.Fatal(err)
	}
}
