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
## Промпт 3.1 — answer-generator scaffold и Dockerfile
**Дата:** 2026-05-20
**Промпт:** Создание Python-сервиса `agents/answer-generator/` с базовой структурой:
`requirements.txt`, `Dockerfile` на базе `python:3.12-slim`.
**Результат:**
**`requirements.txt`** — 7 зависимостей: `nats-py==2.7.2`, `google-generativeai==0.7.2`,
`opentelemetry-api/sdk/exporter-otlp-proto-http==1.24.0`, `python-dotenv==1.0.1`,
`redis==5.0.4`.
**`Dockerfile`**: `python:3.12-slim`, удаление кэша apt, системный пользователь `appuser`,
`WORKDIR /app`, установка зависимостей, `COPY . .`, `chown`, `USER appuser`,
`ENTRYPOINT ["python", "main.py"]`.

---
## Промпт 3.2 — Gemini API клиент с retry
**Дата:** 2026-05-20
**Промпт:** Реализация `gemini_client.py` — клиент Gemini API с системным промптом
юридического помощника и логикой повторных попыток при ошибке.
**Результат:**
Класс **GeminiClient**:
- `__init__`: `genai.configure(api_key=...)`, создание `GenerativeModel("gemini-1.5-flash",
  system_instruction=...)` — системный промпт требует русский язык, использование норм права
  и обязательный дословный disclaimer в конце каждого ответа
- `generate_legal_answer(query, documents)`: формирует prompt из запроса и списка документов;
  4 попытки (начальная + 3 retry) с задержками 0s/1s/2s/4s через `asyncio.to_thread`;
  при полном отказе возвращает шаблон с перечнем документов и disclaimer;
  все ошибки логируются через `logging.warning/error`

---
## Промпт 3.3 — AnswerGeneratorAgent с NATS, Redis, OTel
**Дата:** 2026-05-20
**Промпт:** Реализация `tracer.py`, `agent.py`, `main.py` — полноценный Python-агент
с подпиской на NATS, кэшированием в Redis и OTel-трассировкой.
**Результат:**
**`tracer.py`** — `init_tracer(service_name)`: парсит `JAEGER_ENDPOINT`, строит OTLP URL
`http://{host}:4318/v1/traces`, создаёт `TracerProvider` с `BatchSpanProcessor`,
регистрирует через `trace.set_tracer_provider`.

**`agent.py`** — класс `AnswerGeneratorAgent`:
- `AGENT_ID = "answer-generator-" + uuid4().hex[:8]` на уровне класса
- `start()`: `nats.connect`, Subscribe на `legal.docs.found`, SET Redis status idle,
  `asyncio.create_task(_keepalive)`, блокировка через `asyncio.Event().wait()`
- `_handle_message`: OTel span → parse task/payload → SET busy → `generate_legal_answer` →
  SET `answer:{id}` EX 600 → INCR `tasks_processed` → publish JSON на `legal.answer.raw` →
  SET idle → JSON-лог в `logs/answer-generator.log`
- `_keepalive(nc)`: каждые 30s обновляет `agent:{id}:status` в Redis
- `_write_log`: JSON Lines формат, создаёт `logs/` при необходимости

**`main.py`**: `load_dotenv()` на уровне модуля; `init_tracer`, `redis.from_url`,
`GeminiClient`, `AnswerGeneratorAgent`; `asyncio.run(agent.start())`; `KeyboardInterrupt`
→ `sys.exit(0)`.

**`docker-compose.yml`**: добавлен сервис `answer-generator` с `build context`,
env-переменными (`NATS_URL`, `REDIS_URL`, `JAEGER_ENDPOINT`, `GEMINI_API_KEY`),
`depends_on` nats/redis с `condition: service_healthy`.

---
## Промпт 4.1 — Оркестратор scaffold
**Дата:** 2026-05-20
**Промпт:** Создание `orchestrator/` с `requirements.txt` (11 зависимостей) и `Dockerfile`
на базе `python:3.12-slim`.
**Результат:**
`requirements.txt`: nats-py, fastapi, uvicorn, redis, docker, opentelemetry-api/sdk/exporter,
python-dotenv, pydantic, httpx. `Dockerfile`: slim-образ без non-root пользователя
(оркестратор требует доступ к Docker socket).

---
## Промпт 4.2 — Core orchestrator с NATS
**Дата:** 2026-05-20
**Промпт:** Реализация `orchestrator/orchestrator.py` — управление задачами через NATS
с паттерном Future для ожидания ответов.
**Результат:**
Класс **AgentOrchestrator**: атрибуты `nc`, `rdb`, `pending_tasks: dict[str, Future]`.
**connect()**: подключается к NATS/Redis, подписывается на все 4 выходных топика агентов
(`legal.query.analyzed`, `legal.docs.found`, `legal.answer.raw`, `legal.answer.final`)
через единый `_on_result` — это необходимо для отслеживания результатов каждого шага.
**send_task()**: создаёт Task-словарь (совместим с Go-моделью), сохраняет Future,
публикует в NATS, ждёт через `asyncio.wait_for`; при TimeoutError удаляет из pending_tasks.
**_on_result()**: разрешает Future по `task_id`, проверяет `future.done()` перед set_result.

---
## Промпт 4.3 — Pipeline четырёх шагов с retry
**Дата:** 2026-05-20
**Промпт:** Реализация `orchestrator/pipeline.py` — последовательный запуск 4 агентов
с OTel трассировкой и retry при таймаутах.
**Результат:**
Класс **LegalPipeline.execute(query)**:
- 4 попытки (начальная + 3 retry), задержка 2s между ними при TimeoutError
- Один OTel span `legal_pipeline.execute` оборачивает все 4 шага с атрибутами query/attempt
- Шаги: `send_task("analyze", ..., "legal.query.raw")` →
  `send_task("search", json.loads(result1["output"]), "legal.query.analyzed")` →
  `send_task("generate", json.loads(result2["output"]), "legal.docs.found")` →
  `send_task("check", json.loads(result3["output"]), "legal.answer.raw")` → return result4
- При исчерпании всех попыток пробрасывает последний TimeoutError

---
## Промпт 4.4 — Аукционное распределение задач
**Дата:** 2026-05-20
**Промпт:** Реализация `orchestrator/auction.py` — выбор агента-победителя по минимальной
ставке из данных Redis.
**Результат:**
Dataclass **AgentBid**: `agent_id`, `role`, `bid`, `status`.
Класс **AuctionManager**:
- `get_agent_bids(rdb)`: сканирует `agent:*:status`, для каждого агента читает `tasks_processed`,
  bid = tasks_processed если idle, 1000 если busy; role извлекается из agent_id через rsplit
- `select_winner(bids)`: фильтрует bid < 1000, возвращает min по bid или None
- `log_auction(bids, winner)`: JSON в stdout с `participants` и `winner`

---
## Промпт 4.5 — Динамическое масштабирование через Docker API
**Дата:** 2026-05-20
**Промпт:** Реализация `orchestrator/scaler.py` — автоматический запуск/останов
контейнеров агентов по нагрузке NATS.
**Результат:**
Класс **DynamicScaler**: `SCALE_THRESHOLD = int(env "SCALE_THRESHOLD", "3")`.
**check_and_scale(rdb)**: GET `http://nats:8222/subsz` через httpx.AsyncClient;
`total_pending = data["total_pending"] или data["num_subscriptions"]`;
если pending > threshold → `docker.from_env().containers.run("lab13-universal-agent", detach=True,
environment={AGENT_CONFIG/NATS_URL/REDIS_URL/JAEGER_ENDPOINT}, network="lab13_legal-mas-network")`,
ID в Redis `sadd("scaled_agents", ...)`;
если pending == 0 и scaled_agents > 0 → `spop` + `container.stop()`.

---
## Промпт 4.6 — FastAPI REST API
**Дата:** 2026-05-20
**Промпт:** Реализация `orchestrator/api.py`, `tracer.py`, `main.py` — REST API
оркестратора с 6 эндпоинтами и graceful startup через FastAPI lifespan.
**Результат:**
**`tracer.py`**: аналогично answer-generator, OTLP → `http://{host}:4318/v1/traces`.
**`api.py`**: FastAPI с `asynccontextmanager` lifespan (`set_startup` callback из main.py);
HTTP middleware логирует каждый запрос в JSON (метод/путь/статус/duration_ms);
эндпоинты: `POST /consult` (вызывает pipeline.execute), `GET /health` (nats/redis/agents),
`GET /agents` (scan Redis agent:*:status), `GET /tasks/{id}` (Redis answer:{id} или 404),
`GET /metrics` (sum tasks_processed + agents_online), `GET /auction/demo` (AuctionManager).
**`main.py`**: `load_dotenv()` → module-level инициализация rdb/orchestrator/pipeline/scaler;
`set_startup` регистрирует async startup: `orchestrator.connect()` + `create_task(_scaler_loop)`;
`uvicorn.run(api.app, host="0.0.0.0", port=ORCHESTRATOR_PORT)`.
`docker-compose.yml`: сервис `orchestrator` с портом 8000, Docker socket volume,
env-переменными, `depends_on` nats/redis `service_healthy`.

---
## Промпт 5.1 — Monitoring service scaffold
**Дата:** 2026-05-20
**Промпт:** Создание `monitoring/` с `requirements.txt` (6 зависимостей) и `Dockerfile`
на базе `python:3.12-slim` с non-root пользователем `appuser`.
**Результат:**
`requirements.txt`: fastapi, uvicorn, jinja2, redis, httpx, python-dotenv.
`Dockerfile`: slim-образ, `addgroup/adduser appuser`, `WORKDIR /app`, chown, `USER appuser`,
`ENTRYPOINT ["python", "main.py"]`. В отличие от оркестратора здесь non-root безопасен
(нет Docker socket).

---
## Промпт 5.2 — Redis клиент для агрегации данных
**Дата:** 2026-05-20
**Промпт:** Реализация `monitoring/redis_client.py` — агрегация данных агентов из Redis
для дашборда.
**Результат:**
Класс **MonitoringRedisClient**:
- `get_all_agents()`: SCAN `agent:*:status`; для каждого ключа извлекает agent_id,
  читает status и tasks_processed; роль выводит через `rsplit("-", 1)[0]`;
  возвращает `list[dict]` с полями id/role/status/tasks_processed
- `get_system_metrics()`: вызывает get_all_agents, считает total/online агентов,
  суммирует tasks_processed, читает `SCARD "scaled_agents"`; возвращает dict с
  `total_agents`, `online_agents`, `total_tasks_processed`, `scaled_agents`

---
## Промпт 5.3 — Jinja2 шаблоны и тёмная тема
**Дата:** 2026-05-20
**Промпт:** Реализация FastAPI-приложения (`app.py`, `main.py`), 5 HTML-шаблонов
с наследованием base.html, тёмной темы CSS и JS авторефреша.
**Результат:**
**`templates/base.html`**: Google Fonts (Inter + JetBrains Mono), nav (Dashboard/Agents/
Tasks/Traces), header с `.refresh-dot` (pulse-анимация 2s infinite opacity 1→0.2→1).
**`templates/dashboard.html`**: 3 metric-карточки (agentsOnline/totalTasks/scaledAgents)
с id для JS; agents-grid с `data-agent-id` и `status-{status}` классами; `lastUpdated`.
**`templates/agents.html`**: таблица с badge-статусами (pill-кнопки с rgba-фонами).
**`templates/tasks.html`**: таблица `answer:*` ключей с preview до 150 символов.
**`templates/traces.html`**: ссылка + `<iframe>` на Jaeger UI.
**`static/style.css`**: CSS-переменные `--bg/#0d0d1a`, `--surface/#13132a`, `--accent/#7c6af7`
и т.д.; `.status-idle/busy/offline` border-left; `.status-badge-*` pill-компоненты;
responsive agents-grid (`auto-fill minmax(230px, 1fr)`).
**`static/app.js`**: `setInterval(refreshStats, 5000)`; fetch `/api/stats`; обновляет
метрики, className/textContent карточек агентов, время `lastUpdated`, мигание dot.
**`app.py`**: `BASE_DIR = Path(__file__).parent` для надёжного пути к templates/static;
5 роутов (`/`, `/agents`, `/tasks`, `/traces`, `/api/stats`); `/tasks` сканирует
`answer:*` и формирует preview.
**`main.py`**: `load_dotenv()` → `uvicorn.run(app, host="0.0.0.0", port=MONITORING_PORT)`.
**`docker-compose.yml`**: сервис `monitoring` порт 8080, `REDIS_URL/JAEGER_URL/MONITORING_PORT`,
`depends_on: redis` (без healthcheck condition).

---
## Промпт 6.1 — Финализация Docker Compose
**Дата:** 2026-05-20
**Промпт:** Написание финального `Dockerfile` для Go-агента и добавление четырёх
контейнеров агентов в `docker-compose.yml` с демонстрацией балансировки нагрузки.
**Результат:**
**`agents/universal-agent/Dockerfile`** — двухэтапная сборка:
- `builder` (golang:1.22-alpine): `go mod download` → `go build -ldflags="-w -s"`,
  `CGO_ENABLED=0 GOOS=linux` — статический бинарник без CGO
- Финальный образ (alpine:3.19): `ca-certificates` + `tzdata`, непривилегированный
  `appuser`, копируются бинарник и директория `configs/`

**`docker-compose.yml`** — добавлены 4 сервиса Go-агентов:
- `query-analyzer`: `build context ./agents/universal-agent`, `image: lab13-universal-agent`
  (метка образа для переиспользования), `AGENT_CONFIG=/app/configs/query-analyzer.md`,
  `depends_on` nats/redis `service_healthy`
- `query-analyzer-2`: `image: lab13-universal-agent` (без build), те же конфиг и топик;
  `depends_on: query-analyzer` гарантирует, что образ уже собран
- `document-searcher`: `AGENT_CONFIG=/app/configs/document-searcher.md`
- `contradiction-checker`: `AGENT_CONFIG=/app/configs/contradiction-checker.md`
Все используют общую сеть `legal-mas-network`, `restart: unless-stopped`.

**Балансировка нагрузки**: оба `query-analyzer` подписаны на `legal.query.raw`.
NATS распределяет сообщения round-robin автоматически — без доп. конфигурации.
Динамически поднятые `DynamicScaler`-ом контейнеры присоединяются к той же балансировке.

**`README.md`**: добавлен раздел «Демонстрация балансировки нагрузки» с командой
`docker compose logs -f query-analyzer query-analyzer-2`.

**Итоговый состав системы** (`docker compose up --build`):
nats · redis · jaeger · query-analyzer · query-analyzer-2 ·
document-searcher · contradiction-checker · answer-generator ·
orchestrator · monitoring = **10 сервисов**.

---
