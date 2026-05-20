package models

import "time"

// Task описывает единицу работы, передаваемую между агентами через NATS.
type Task struct {
	ID          string            `json:"id"`
	Type        string            `json:"type"`
	Payload     string            `json:"payload"`
	TraceID     string            `json:"trace_id"`
	SpanID      string            `json:"span_id"`
	Pipeline    []string          `json:"pipeline"`
	CurrentStep int               `json:"current_step"`
	Metadata    map[string]string `json:"metadata"`
	CreatedAt   time.Time         `json:"created_at"`
}

// Result содержит итог обработки задачи одним агентом.
type Result struct {
	TaskID      string    `json:"task_id"`
	AgentID     string    `json:"agent_id"`
	AgentRole   string    `json:"agent_role"`
	Success     bool      `json:"success"`
	Output      string    `json:"output"`
	Error       string    `json:"error,omitempty"`
	TraceID     string    `json:"trace_id"`
	DurationMs  int64     `json:"duration_ms"`
	ProcessedAt time.Time `json:"processed_at"`
}
