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
## Промпт 1.1 — Docker Compose инфраструктура
**Дата:** 2026-05-20
**Промпт:** Создание инфраструктурного слоя проекта: заполнение `docker-compose.yml`
тремя сервисами (NATS, Redis, Jaeger) и добавление многоэтапных Dockerfile для
Go- и Python-сервисов в директорию `docker/`.
**Результат:**
Файл **`docker-compose.yml`** заменён со следующими сервисами:
- `nats` (image: `nats:2.10-alpine`) — брокер сообщений с JetStream, порты 4222/8222,
  healthcheck через `nc -z localhost 4222` (interval 5s, timeout 3s, retries 5)
- `redis` (image: `redis:7-alpine`) — кэш сессий с `appendonly yes`, `maxmemory 256mb`,
  политика `allkeys-lru`, порт 6379, named volume `redis-data`, healthcheck `redis-cli ping`
- `jaeger` (image: `jaegertracing/all-in-one:1.57`) — распределённая трассировка,
  `COLLECTOR_OTLP_ENABLED=true`, порты 16686 (UI), 14268, 4317, 4318
Все сервисы подключены к сети `legal-mas-network` (driver: bridge).
Named volume: `redis-data`.

Файл **`docker/go-agent.Dockerfile`** — многоэтапная сборка Go-агента:
- Этап `builder` (golang:1.22-alpine): загрузка зависимостей, сборка с флагами
  `CGO_ENABLED=0 GOOS=linux -ldflags="-w -s"` (минимальный бинарник без отладочных символов)
- Финальный образ (alpine:3.19): только `ca-certificates` и `tzdata`, непривилегированный
  пользователь `appuser`, копируются бинарник и директория `configs/`

Файл **`docker/python.Dockerfile`** — образ для Python-сервисов:
- Base: `python:3.12-slim`, установка `curl` и `gcc` без рекомендуемых пакетов
- Непривилегированный пользователь `appuser`, зависимости через `requirements.txt`

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
## Промпт 2.4 — OpenTelemetry трассировка
**Дата:** 2026-05-20
**Промпт:** Реализация `internal/tracing/tracer.go` — инициализация TracerProvider
с OTLP HTTP-экспортёром для Jaeger.
**Результат:**
Создана функция **InitTracer(serviceName string) (*sdktrace.TracerProvider, error)**:
- `otlptracehttp.New` с `WithEndpoint` и `WithInsecure()` — без TLS внутри Docker-сети
- Endpoint извлекается из `JAEGER_ENDPOINT` через `resolveEndpoint`: парсит URL и берёт
  `host:port`; если переменная не задана — дефолт `jaeger:4318` (OTLP HTTP порт)
- `resource.New` с атрибутами `service.name=serviceName`, `service.version="1.0.0"`
- `sdktrace.WithBatcher(exporter)` — пакетная отправка спанов
- При ошибке создания resource — корректно завершает exporter перед возвратом ошибки
Вспомогательная функция `resolveEndpoint` отделяет парсинг URL от основной логики.

---
## Промпт 2.5 — Processor с логикой четырёх типов агентов
**Дата:** 2026-05-20
**Промпт:** Реализация `internal/agent/processor.go` — обработка задач для всех четырёх
типов агентов с встроенной базой юридических документов.
**Результат:**
Переменная **legalDatabase** — встроенная база из 5 категорий:
`трудовое` (3 статьи ТК РФ), `гражданское` (3 статьи ГК РФ), `уголовное` (3 статьи УК РФ),
`административное` (2 статьи КоАП РФ), `общее` (Конституция + ГК РФ).

Функция **ProcessTask(cfg, task)** — switch по `cfg.AgentType`:
- `query-analyzer`: определяет тип вопроса по ключевым словам через `strings.ToLower` +
  `containsAny`; возвращает JSON `{query_type, urgency, original_query}`
- `document-searcher`: парсит payload как JSON, извлекает `query_type`, ищет в базе;
  при отсутствии ключа — возвращает категорию "общее"; JSON `{documents, query_type, source}`
- `contradiction-checker`: проверяет наличие подстроки `disclaimer`; без неё —
  `contradictions_found=true, quality_score=40`; с ней — `false, 90`; JSON с `notes`
- default: строка `"Агент {role}: получено задание {id}, payload: {payload}"`

Во всех случаях `Result.Success=true`, `TaskID`, `AgentRole`, `TraceID`, `ProcessedAt` заполнены.

---
## Промпт 2.6 — Agent core: NATS, Redis, JSON-логирование
**Дата:** 2026-05-20
**Промпт:** Реализация `internal/agent/agent.go` — основная структура агента
с подпиской на NATS, хранением статуса в Redis и JSON-логированием.
**Результат:**
Структура **Agent**: `id`, `cfg`, `nc *nats.Conn`, `rdb *redis.Client`,
`tracer trace.Tracer`, `tp *sdktrace.TracerProvider`, `logFile *os.File`,
`mu sync.Mutex`, `status string`.

**NewAgent(cfg)**: подключение к NATS (env `NATS_URL`, дефолт `nats.DefaultURL`),
Redis (env `REDIS_URL` через `redis.ParseURL`, дефолт `redis://redis:6379`),
трейсер через `InitTracer`; ID = `agentType-{uuid[:8]}`; создание `logs/`
через `os.MkdirAll`; открытие лог-файла с флагами `O_APPEND|O_CREATE|O_WRONLY`.

**Start(ctx)**: SET `agent:{id}:status "idle" EX 60`, Subscribe на `InputTopic`,
keepalive-горутина каждые 30s обновляет TTL через mutex-protected `a.status`,
блокируется на `<-ctx.Done()`, затем `Unsubscribe`, `nc.Close`, `logFile.Close`,
`tp.Shutdown`.

**handleMessage**: десериализация Task, создание OTel span с атрибутами
`agent.id/role`, `task.id/type`; SET status "busy"; `ProcessTask`;
`INCR agent:{id}:tasks_processed`; заполнение `AgentID/DurationMs/ProcessedAt`;
Publish JSON в `OutputTopic`; SET status "idle"; запись JSON-лога в файл.

---
## Промпт 2.7 — main.go с graceful shutdown
**Дата:** 2026-05-20
**Промпт:** Реализация `main.go` — точки входа с загрузкой конфигурации
и graceful shutdown по сигналам ОС.
**Результат:**
- `godotenv.Load()` — ошибка игнорируется (`_ =`), переменные берутся из Docker-окружения
- Чтение `AGENT_CONFIG` из env → `config.LoadConfig(path)` → `log.Fatalf` при ошибке
- `agent.NewAgent(cfg)` → `log.Fatalf` при ошибке
- `signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)` —
  контекст отменяется при Ctrl+C или `docker stop`; `defer stop()` освобождает ресурсы
- `a.Start(ctx)` блокируется до сигнала, затем корректно завершает NATS, Redis, трейсер
`go build ./...` завершился без ошибок после `go mod tidy`.

---
## Промпт 2.8 — Конфиги ролей агентов
**Дата:** 2026-05-20
**Промпт:** Заполнение четырёх Markdown-файлов конфигурации в `configs/`,
определяющих роли агентов в pipeline юридической консультации.
**Результат:**
Все файлы содержат секции `# Role`, `## Agent Type`, `## Input Topic`,
`## Output Topic`, `## Rules`, `## Description` — якоря для `config.LoadConfig`.

**`configs/query-analyzer.md`** — роль «Анализатор юридических запросов»:
- AgentType: `query-analyzer`, топики: `legal.query.raw` → `legal.query.analyzed`
- Классифицирует запрос по 5 категориям, оценивает срочность

**`configs/document-searcher.md`** — роль «Поисковик по правовой базе»:
- AgentType: `document-searcher`, топики: `legal.query.analyzed` → `legal.docs.found`
- Ищет статьи законодательства по полю `query_type` из payload

**`configs/answer-generator.md`** — роль «Генератор юридических ответов»:
- AgentType: `answer-generator`, топики: `legal.docs.found` → `legal.answer.raw`
- Формирует структурированный ответ с обязательным disclaimer; LLM на Python + Gemini API

**`configs/contradiction-checker.md`** — роль «Проверщик противоречий»:
- AgentType: `contradiction-checker`, топики: `legal.answer.raw` → `legal.answer.final`
- Проверяет наличие disclaimer, выставляет `quality_score` 90 или 40

Pipeline целиком: `legal.query.raw` → `legal.query.analyzed` → `legal.docs.found`
→ `legal.answer.raw` → `legal.answer.final`.

---
