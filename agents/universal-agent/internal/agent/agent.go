package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/google/uuid"
	nats "github.com/nats-io/nats.go"
	"github.com/redis/go-redis/v9"
	"go.opentelemetry.io/otel/attribute"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/trace"

	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/config"
	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/models"
	agenttracing "github.com/Dev66-66/LAB13/agents/universal-agent/internal/tracing"
)

// Agent универсальный агент: подписывается на NATS, обрабатывает задачи,
// хранит статус в Redis и отправляет трейсы в Jaeger.
type Agent struct {
	id      string
	cfg     config.AgentConfig
	nc      *nats.Conn
	rdb     *redis.Client
	tracer  trace.Tracer
	tp      *sdktrace.TracerProvider
	logFile *os.File
	mu      sync.Mutex
	status  string
}

// NewAgent создаёт агента: подключает NATS и Redis, инициализирует трейсер,
// открывает лог-файл в директории logs/.
func NewAgent(cfg config.AgentConfig) (*Agent, error) {
	natsURL := os.Getenv("NATS_URL")
	if natsURL == "" {
		natsURL = nats.DefaultURL
	}
	nc, err := nats.Connect(natsURL)
	if err != nil {
		return nil, fmt.Errorf("не удалось подключиться к NATS (%s): %w", natsURL, err)
	}

	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://redis:6379"
	}
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		nc.Close()
		return nil, fmt.Errorf("неверный REDIS_URL: %w", err)
	}
	rdb := redis.NewClient(opt)

	tp, err := agenttracing.InitTracer(cfg.Role)
	if err != nil {
		nc.Close()
		return nil, fmt.Errorf("не удалось инициализировать трейсер: %w", err)
	}

	id := cfg.AgentType + "-" + uuid.New().String()[:8]

	if err := os.MkdirAll("logs", 0755); err != nil {
		nc.Close()
		return nil, fmt.Errorf("не удалось создать директорию logs: %w", err)
	}

	logFile, err := os.OpenFile(
		"logs/agent-"+id+".log",
		os.O_APPEND|os.O_CREATE|os.O_WRONLY,
		0644,
	)
	if err != nil {
		nc.Close()
		return nil, fmt.Errorf("не удалось открыть лог-файл: %w", err)
	}

	return &Agent{
		id:      id,
		cfg:     cfg,
		nc:      nc,
		rdb:     rdb,
		tracer:  tp.Tracer(cfg.Role),
		tp:      tp,
		logFile: logFile,
		status:  "idle",
	}, nil
}

// Start регистрирует агента в Redis, запускает keepalive-горутину,
// подписывается на входящий топик и блокируется до отмены контекста.
func (a *Agent) Start(ctx context.Context) error {
	bgCtx := context.Background()

	a.setRedisStatus(bgCtx, "idle")

	sub, err := a.nc.Subscribe(a.cfg.InputTopic, a.handleMessage)
	if err != nil {
		return fmt.Errorf("не удалось подписаться на топик %s: %w", a.cfg.InputTopic, err)
	}

	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				a.mu.Lock()
				status := a.status
				a.mu.Unlock()
				a.rdb.Set(bgCtx, "agent:"+a.id+":status", status, 60*time.Second)
			case <-ctx.Done():
				return
			}
		}
	}()

	<-ctx.Done()

	sub.Unsubscribe()
	a.nc.Close()
	if a.logFile != nil {
		a.logFile.Close()
	}
	if a.tp != nil {
		a.tp.Shutdown(bgCtx)
	}
	return nil
}

func (a *Agent) handleMessage(msg *nats.Msg) {
	var task models.Task
	if err := json.Unmarshal(msg.Data, &task); err != nil {
		return
	}

	ctx, span := a.tracer.Start(context.Background(), "agent.process_task",
		trace.WithAttributes(
			attribute.String("agent.id", a.id),
			attribute.String("agent.role", a.cfg.Role),
			attribute.String("task.id", task.ID),
			attribute.String("task.type", task.Type),
		),
	)
	defer span.End()

	a.setRedisStatus(ctx, "busy")
	start := time.Now()

	result := ProcessTask(a.cfg, task)

	a.rdb.Incr(ctx, "agent:"+a.id+":tasks_processed")

	result.AgentID = a.id
	result.DurationMs = time.Since(start).Milliseconds()
	result.ProcessedAt = time.Now()

	if data, err := json.Marshal(result); err == nil {
		a.nc.Publish(a.cfg.OutputTopic, data)
	}

	a.setRedisStatus(ctx, "idle")
	a.writeLog(task, result)
}

func (a *Agent) setRedisStatus(ctx context.Context, status string) {
	a.mu.Lock()
	a.status = status
	a.mu.Unlock()
	a.rdb.Set(ctx, "agent:"+a.id+":status", status, 60*time.Second)
}

func (a *Agent) writeLog(task models.Task, result models.Result) {
	if a.logFile == nil {
		return
	}
	entry, _ := json.Marshal(map[string]interface{}{
		"timestamp":   time.Now().Format(time.RFC3339),
		"level":       "INFO",
		"agent_id":    a.id,
		"agent_role":  a.cfg.Role,
		"task_id":     task.ID,
		"duration_ms": result.DurationMs,
		"message":     "task processed",
	})
	a.logFile.Write(append(entry, '\n'))
}
