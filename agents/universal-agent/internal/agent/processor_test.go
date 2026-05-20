package agent

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/config"
	"github.com/Dev66-66/LAB13/agents/universal-agent/internal/models"
)

func TestProcessTask_QueryAnalyzer_LaborLaw(t *testing.T) {
	cfg := config.AgentConfig{Role: "Анализатор", AgentType: "query-analyzer"}
	task := models.Task{ID: "t1", Payload: "Меня незаконно уволили"}
	result := ProcessTask(cfg, task)
	if !result.Success {
		t.Fatalf("expected Success=true, got false")
	}
	if !strings.Contains(result.Output, "трудовое") {
		t.Errorf("expected Output to contain 'трудовое', got: %s", result.Output)
	}
}

func TestProcessTask_QueryAnalyzer_CivilLaw(t *testing.T) {
	cfg := config.AgentConfig{Role: "Анализатор", AgentType: "query-analyzer"}
	task := models.Task{ID: "t2", Payload: "Контрагент не платит по договору"}
	result := ProcessTask(cfg, task)
	if !strings.Contains(result.Output, "гражданское") {
		t.Errorf("expected Output to contain 'гражданское', got: %s", result.Output)
	}
}

func TestProcessTask_DocumentSearcher_ReturnsDocuments(t *testing.T) {
	cfg := config.AgentConfig{Role: "Поисковик", AgentType: "document-searcher"}
	payload := `{"query_type":"трудовое","original_query":"тест"}`
	task := models.Task{ID: "t3", Payload: payload}
	result := ProcessTask(cfg, task)
	if !strings.Contains(result.Output, "ТК РФ") {
		t.Errorf("expected Output to contain 'ТК РФ', got: %s", result.Output)
	}
}

func TestProcessTask_ContradictionChecker_MissingDisclaimer(t *testing.T) {
	cfg := config.AgentConfig{Role: "Верификатор", AgentType: "contradiction-checker"}
	task := models.Task{ID: "t4", Payload: "Вот ответ без нужного слова"}
	result := ProcessTask(cfg, task)
	if !strings.Contains(result.Output, "true") {
		t.Errorf("expected Output to contain 'true' (contradictions_found), got: %s", result.Output)
	}
}

func TestProcessTask_ContradictionChecker_WithDisclaimer(t *testing.T) {
	cfg := config.AgentConfig{Role: "Верификатор", AgentType: "contradiction-checker"}
	task := models.Task{ID: "t5", Payload: "Вот ответ. Disclaimer: носит информационный характер."}
	result := ProcessTask(cfg, task)
	var out map[string]interface{}
	if err := json.Unmarshal([]byte(result.Output), &out); err != nil {
		t.Fatalf("failed to parse Output JSON: %v", err)
	}
	score, ok := out["quality_score"].(float64)
	if !ok {
		t.Fatalf("quality_score not found or not a number in: %s", result.Output)
	}
	if score < 70 {
		t.Errorf("expected quality_score >= 70, got %v", score)
	}
}
