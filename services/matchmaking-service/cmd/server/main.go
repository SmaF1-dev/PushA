package main

import (
	"log"
	"net/http"
	_ "pusha/matchmaking-service/docs"
	"pusha/matchmaking-service/internal/api"
	"pusha/matchmaking-service/internal/api/handlers"
	"pusha/matchmaking-service/internal/config"
	"pusha/matchmaking-service/internal/db"
	"pusha/matchmaking-service/internal/provider"
	"pusha/matchmaking-service/internal/repository"
	"pusha/matchmaking-service/internal/service"
)

// @title PushA Matchmaking Service API
// @version 1.0
// @description REST API for Valorant teammate matchmaking. The service creates matchmaking requests, retrieves candidates from the Python Player Service via gRPC, scores and filters them, and creates match groups.
// @host localhost:8080
// @BasePath /api/v1
// @schemes http
func main() {
	cfg := config.Load()

	postgresPool, err := db.NewPostgresPool(cfg.DatabaseURL)
	if err != nil {
		log.Fatal("failed to connect to PostgreSQL: ", err)
	}
	defer postgresPool.Close()

	matchmakingRepository := repository.NewMatchmakingRepository(postgresPool)
	candidateRepository := repository.NewCandidateRepository(postgresPool)
	playerProvider, err := provider.NewGrpcPlayerProvider(cfg.PlayerServiceGRPCAddr)
	if err != nil {
		log.Fatal("failed to create player service grpc provider: ", err)
	}
	defer playerProvider.Close()
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
