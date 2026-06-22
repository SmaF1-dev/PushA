package main

import (
	"log"
	"net/http"
	"pusha/matchmaking-service/internal/api"
	"pusha/matchmaking-service/internal/api/handlers"
	"pusha/matchmaking-service/internal/config"
	"pusha/matchmaking-service/internal/db"
	"pusha/matchmaking-service/internal/repository"
)

func main() {
	cfg := config.Load()

	postgresPool, err := db.NewPostgresPool(cfg.DatabaseURL)
	if err != nil {
		log.Fatal("failed to connect to PostgreSQL: ", err)
	}
	defer postgresPool.Close()

	matchmakingRepository := repository.NewMatchmakingRepository(postgresPool)
	matchmakingHandler := handlers.NewMatchmakingHandler(matchmakingRepository)

	router := api.NewRouter(matchmakingHandler)

	addr := ":" + cfg.HTTPPort

	log.Println("Matchmaking service started on", addr)

	err = http.ListenAndServe(addr, router)
	if err != nil {
		log.Fatal(err)
	}
}
