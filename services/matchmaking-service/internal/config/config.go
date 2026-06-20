package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	HTTPPort              string `json:"http_port"`
	PlayerServiceGRPCAddr string `json:"player_service_grppc_addr"`
}

func Load() Config {
	err := godotenv.Load()
	if err != nil {
		log.Println("No .env file found.")
	}

	return Config{
		HTTPPort:              getEnv("HTTP_PORT", "8080"),
		PlayerServiceGRPCAddr: getEnv("PLAYER_SERVICE_GRPC_ADDR", "localhost:50051"),
	}
}

func getEnv(key string, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
