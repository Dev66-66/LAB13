package agent

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/config"
	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/models"
)

var legalDatabase = map[string][]string{
	"трудовое": {
		"ТК РФ ст.77 — Основания прекращения трудового договора",
		"ТК РФ ст.81 — Расторжение по инициативе работодателя",
		"ТК РФ ст.140 — Сроки расчёта при увольнении",
	},
	"гражданское": {
		"ГК РФ ст.309 — Исполнение обязательств",
		"ГК РФ ст.395 — Ответственность за неисполнение денежного обязательства",
		"ГК РФ ст.196 — Общий срок исковой давности",
	},
	"уголовное": {
		"УК РФ ст.105 — Убийство",
		"УК РФ ст.158 — Кража",
		"УК РФ ст.159 — Мошенничество",
	},
	"административное": {
		"КоАП РФ ст.12.9 — Превышение скорости",
		"КоАП РФ ст.20.1 — Мелкое хулиганство",
	},
	"общее": {
		"Конституция РФ ст.48 — Право на юридическую помощь",
		"ГК РФ ст.12 — Способы защиты гражданских прав",
	},
}

// ProcessTask выполняет задачу согласно типу агента, указанному в конфигурации.
func ProcessTask(cfg config.AgentConfig, task models.Task) models.Result {
	result := models.Result{
		TaskID:      task.ID,
		AgentRole:   cfg.Role,
		Success:     true,
		TraceID:     task.TraceID,
		ProcessedAt: time.Now(),
	}

	switch cfg.AgentType {
	case "query-analyzer":
		result.Output = analyzeQuery(task)
	case "document-searcher":
		result.Output = searchDocuments(task)
	case "contradiction-checker":
		result.Output = checkContradictions(task)
	default:
		result.Output = fmt.Sprintf("Агент %s: получено задание %s, payload: %s",
			cfg.Role, task.ID, task.Payload)
	}

	return result
}

func analyzeQuery(task models.Task) string {
	payload := strings.ToLower(task.Payload)

	var queryType string
	switch {
	case containsAny(payload, "трудов", "увольн", "работодат"):
		queryType = "трудовое"
	case containsAny(payload, "уголовн", "преступл", "арест"):
		queryType = "уголовное"
	case containsAny(payload, "гражданск", "договор", "долг"):
		queryType = "гражданское"
	case containsAny(payload, "административн", "штраф"):
		queryType = "административное"
	default:
		queryType = "общее"
	}

	out, _ := json.Marshal(map[string]string{
		"query_type":     queryType,
		"urgency":        "средняя",
		"original_query": task.Payload,
	})
	return string(out)
}

func searchDocuments(task models.Task) string {
	var parsed map[string]interface{}
	queryType := "общее"
	if json.Unmarshal([]byte(task.Payload), &parsed) == nil {
		if qt, ok := parsed["query_type"].(string); ok {
			queryType = qt
		}
	}

	docs, ok := legalDatabase[queryType]
	if !ok {
		docs = legalDatabase["общее"]
	}

	out, _ := json.Marshal(map[string]interface{}{
		"documents":  docs,
		"query_type": queryType,
		"source":     "database",
	})
	return string(out)
}

func checkContradictions(task models.Task) string {
	hasDisclaimer := strings.Contains(strings.ToLower(task.Payload), "disclaimer")

	contradictionsFound := !hasDisclaimer
	qualityScore := 40
	notes := "Обнаружены потенциальные противоречия, требуется проверка"
	if hasDisclaimer {
		qualityScore = 90
		notes = "Документ содержит оговорки, противоречия не обнаружены"
	}

	out, _ := json.Marshal(map[string]interface{}{
		"contradictions_found": contradictionsFound,
		"quality_score":        qualityScore,
		"notes":                notes,
	})
	return string(out)
}

func containsAny(s string, subs ...string) bool {
	for _, sub := range subs {
		if strings.Contains(s, sub) {
			return true
		}
	}
	return false
}
