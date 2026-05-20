package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"

	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/agent"
	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/config"
)

func main() {
	// Не падаем при отсутствии .env — переменные могут приходить из Docker
	_ = godotenv.Load()

	configPath := os.Getenv("AGENT_CONFIG")
	if configPath == "" {
		log.Fatal("AGENT_CONFIG environment variable is not set")
	}

	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		log.Fatalf("не удалось загрузить конфигурацию: %v", err)
	}

	a, err := agent.NewAgent(cfg)
	if err != nil {
		log.Fatalf("не удалось создать агент: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	if err := a.Start(ctx); err != nil {
		log.Fatalf("ошибка выполнения агента: %v", err)
	}
}
