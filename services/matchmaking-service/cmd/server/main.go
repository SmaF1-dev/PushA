package main

import (
	"log"
	"net/http"
	"pusha/matchmaking-service/internal/api"
	"pusha/matchmaking-service/internal/config"
)

func main() {
	cfg := config.Load()
	router := api.NewRouter()

	addr := ":" + cfg.HTTPPort

	log.Println("Matchmaking service started on", addr)

	err := http.ListenAndServe(addr, router)
	if err != nil {
		log.Fatal(err)
	}
}
