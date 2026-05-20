package config

import (
	"fmt"
	"os"
	"strings"
)

// AgentConfig хранит настройки роли агента, загруженные из Markdown-файла.
type AgentConfig struct {
	Role        string
	AgentType   string
	InputTopic  string
	OutputTopic string
	Rules       string
	Description string
}

// LoadConfig читает Markdown-файл по указанному пути и парсит секции
// по заголовкам в поля AgentConfig. Возвращает ошибку, если Role или
// AgentType отсутствуют.
func LoadConfig(path string) (AgentConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return AgentConfig{}, fmt.Errorf("не удалось прочитать файл конфигурации %s: %w", path, err)
	}

	lines := strings.Split(string(data), "\n")
	var cfg AgentConfig

	currentHeader := ""
	var sectionLines []string

	flush := func() {
		value := strings.TrimSpace(strings.Join(sectionLines, "\n"))
		switch currentHeader {
		case "# Role":
			cfg.Role = value
		case "## Agent Type":
			cfg.AgentType = value
		case "## Input Topic":
			cfg.InputTopic = value
		case "## Output Topic":
			cfg.OutputTopic = value
		case "## Rules":
			cfg.Rules = value
		case "## Description":
			cfg.Description = value
		}
		sectionLines = nil
	}

	for _, line := range lines {
		if strings.HasPrefix(line, "# ") || strings.HasPrefix(line, "## ") {
			flush()
			currentHeader = strings.TrimRight(line, "\r")
		} else {
			sectionLines = append(sectionLines, line)
		}
	}
	flush()

	if cfg.Role == "" || cfg.AgentType == "" {
		return AgentConfig{}, fmt.Errorf("конфигурация %s не содержит обязательных полей Role или AgentType", path)
	}

	return cfg, nil
}
