package main

import (
	"log"
	"net/http"
	"pusha/matchmaking-service/internal/api"
	"pusha/matchmaking-service/internal/config"
	"pusha/matchmaking-service/internal/db"
)

func main() {
	cfg := config.Load()

	postgresPool, err := db.NewPostgresPool(cfg.DatabaseURL)
	if err != nil {
		log.Fatal("failed to connect to PostgreSQL: ", err)
	}
	defer postgresPool.Close()

	router := api.NewRouter()

	addr := ":" + cfg.HTTPPort

	log.Println("Matchmaking service started on", addr)

	err = http.ListenAndServe(addr, router)
	if err != nil {
		log.Fatal(err)
	}
}
