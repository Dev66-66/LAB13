# Prompt Log — Лабораторная работа №13
Журнал выполненных промптов.
---
## Промпт 0.1 — Инициализация проекта
**Дата:** 2026-05-19
**Промпт:** Инициализация git-репозитория для проекта «Юридическая консультация».
Создание файловой структуры LAB13/, .gitignore, .env.example, README.md, PROMPT_LOG.md.
**Результат:**
Созданы следующие файлы и директории:

**Директории:**
- `LAB13/agents/universal-agent/configs/` — конфигурационные промпты агентов
- `LAB13/orchestrator/` — директория оркестратора (`.gitkeep`)
- `LAB13/monitoring/` — директория мониторинга (`.gitkeep`)
- `LAB13/docker/` — директория Docker-конфигов (`.gitkeep`)
- `LAB13/docs/` — директория документации (`.gitkeep`)

**Файлы-заглушки:**
- `LAB13/agents/universal-agent/configs/query-analyzer.md`
- `LAB13/agents/universal-agent/configs/document-searcher.md`
- `LAB13/agents/universal-agent/configs/answer-generator.md`
- `LAB13/agents/universal-agent/configs/contradiction-checker.md`
- `LAB13/agents/universal-agent/Dockerfile`
- `LAB13/docker-compose.yml`

**`.gitignore`** содержит правила для: Go (*.exe, *.out, /bin/, /vendor/, *.test),
Python (__pycache__/, *.pyc, .venv/, dist/, .pytest_cache/, .mypy_cache/),
IDE (.idea/, .vscode/, *.swp, .DS_Store, Thumbs.db),
секреты и логи (.env, *.log, logs/, tmp/),
Docker-тома (data/, docker-volumes/).

**`.env.example`** содержит 10 переменных: GEMINI_API_KEY, NATS_URL, REDIS_URL,
JAEGER_ENDPOINT, MAX_QUEUE_LENGTH, SCALE_THRESHOLD, LOG_LEVEL,
ORCHESTRATOR_PORT, MONITORING_PORT, AGENT_TIMEOUT_SEC.

**`README.md`** содержит: заголовок, данные студента, описание 4 агентов,
ASCII-диаграмму pipeline, таблицу технологического стека (Go 1.22 / Python 3.12 /
NATS 2.10 / Redis 7 / Jaeger 1.57 / Gemini API / FastAPI / Docker Compose),
раздел «Быстрый старт», таблицу переменных окружения, дерево структуры проекта.

**Git-команды и их вывод:**
```
git init
  → Initialized empty Git repository in C:/users/maksv/LAB13/.git/

git remote add origin https://github.com/Dev66-66/LAB13.git

git add .

git commit -m "feat: init project structure, .gitignore, .env.example"
  → [main (root-commit) <hash>] feat: init project structure, .gitignore, .env.example
     17 files changed, ...

git push -u origin main
  → Branch 'main' set up to track remote branch 'main' from 'origin'.
```
---
## Промпт 2.1 — Инициализация Go-модуля
**Дата:** 2026-05-20
**Промпт:** Инициализация Go-модуля для универсального агента в `agents/universal-agent/`.
Установка зависимостей: nats.go, go-redis, opentelemetry (otel, sdk, otlptrace, otlptracehttp, trace), godotenv, uuid.
**Результат:**
Выполнено `go mod init github.com/Dev66-66/LAB13/agents/universal-agent`.
Добавлены зависимости (зафиксированы в `go.mod` и `go.sum`):
- `github.com/nats-io/nats.go v1.34.0` — клиент NATS
- `github.com/redis/go-redis/v9 v9.5.1` — клиент Redis
- `go.opentelemetry.io/otel v1.24.0` — ядро OpenTelemetry
- `go.opentelemetry.io/otel/sdk v1.24.0` — SDK для трассировщика
- `go.opentelemetry.io/otel/trace v1.24.0` — API трассировки
- `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp v1.24.0` — HTTP-экспортёр в Jaeger
- `github.com/joho/godotenv v1.5.1` — загрузка `.env`
- `github.com/google/uuid v1.6.0` — генерация идентификаторов задач
`go build ./...` завершился без ошибок.

---
## Промпт 2.2 — Модели данных Task и Result
**Дата:** 2026-05-20
**Промпт:** Создание файла `internal/models/task.go` с двумя структурами данных,
сериализуемыми в JSON и передаваемыми через NATS.
**Результат:**
Создан `agents/universal-agent/internal/models/task.go`, пакет `models`.
Структура **Task** — единица работы в pipeline:
- `ID`, `Type`, `Payload` — идентификация и содержимое задачи
- `TraceID`, `SpanID` — контекст распределённой трассировки
- `Pipeline []string`, `CurrentStep int` — описание и позиция в цепочке агентов
- `Metadata map[string]string` — произвольные метаданные
- `CreatedAt time.Time` — метка создания
Структура **Result** — результат обработки задачи одним агентом:
- `TaskID`, `AgentID`, `AgentRole` — связь с задачей и агентом
- `Success bool`, `Output string`, `Error string (omitempty)` — исход обработки
- `TraceID string`, `DurationMs int64` — данные для трассировки и мониторинга
- `ProcessedAt time.Time` — метка завершения обработки

---
## Промпт 2.3 — Markdown config loader
**Дата:** 2026-05-20
**Промпт:** Создание `internal/config/loader.go` — парсер Markdown-файлов конфигурации
агентских ролей (из директории `configs/`).
**Результат:**
Создан `agents/universal-agent/internal/config/loader.go`, пакет `config`.
Структура **AgentConfig** содержит поля: `Role`, `AgentType`, `InputTopic`, `OutputTopic`, `Rules`, `Description`.
Функция **LoadConfig(path string) (AgentConfig, error)**:
- Читает файл через `os.ReadFile`
- Разбивает по строкам, отслеживает текущий заголовок (`# ...` или `## ...`)
- При смене заголовка накопленные строки `flush`-ятся в соответствующее поле
- Маппинг: `# Role` → `Role`, `## Agent Type` → `AgentType`, `## Input Topic` → `InputTopic`,
  `## Output Topic` → `OutputTopic`, `## Rules` → `Rules`, `## Description` → `Description`
- Если `Role` или `AgentType` пустые — возвращает описательную ошибку
Также созданы файлы-заглушки: `main.go`, `internal/tracing/tracer.go`,
`internal/agent/agent.go`, `internal/agent/processor.go`.

---
