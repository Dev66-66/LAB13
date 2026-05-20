# Лабораторная работа №13 — Мультиагентные системы

## Данные студента

| Поле               | Значение                      |
|--------------------|-------------------------------|
| ФИО                | Фомичев Ярослав Николаевич    |
| Группа             | 221131                        |
| Вариант            | 21                            |
| Предметная область | Юридическая консультация      |
| Сложность          | Повышенная                    |

---

## Описание системы

Система реализует автоматизированную юридическую консультацию на основе мультиагентного pipeline. Входящий HTTP-запрос с юридическим вопросом последовательно обрабатывается четырьмя специализированными агентами:

| Агент                   | Роль в pipeline                                                                 |
|-------------------------|---------------------------------------------------------------------------------|
| **query-analyzer**      | Разбирает вопрос пользователя, определяет тип правового запроса и ключевые сущности (нормы, стороны, юрисдикция) |
| **document-searcher**   | Ищет релевантные нормативные акты, судебные прецеденты и правовые документы в базе знаний |
| **answer-generator**    | Формирует развёрнутый юридический ответ на основе найденных документов с использованием Gemini API |
| **contradiction-checker** | Проверяет итоговый ответ на внутренние противоречия, актуальность ссылок и соответствие действующему законодательству |

Агенты общаются через брокер сообщений **NATS**. Состояние сессий кэшируется в **Redis**. Трассировка запросов ведётся через **Jaeger**. Оркестратор управляет маршрутизацией и авто-масштабированием агентов по очереди.

---

## Pipeline

```
HTTP запрос → Оркестратор → query-analyzer → document-searcher
                                                     │
                                                     ▼
              HTTP ответ ← contradiction-checker ← answer-generator
```

---

## Технологический стек

| Компонент        | Версия       | Назначение                              |
|------------------|--------------|-----------------------------------------|
| Go               | 1.22         | Оркестратор и агенты (ядро логики)      |
| Python           | 3.12         | Агент генерации ответов (Gemini API)    |
| NATS             | 2.10         | Брокер сообщений между агентами         |
| Redis            | 7            | Кэш сессий и промежуточных результатов  |
| Jaeger           | 1.57         | Распределённая трассировка запросов     |
| Gemini API       | —            | LLM для генерации юридических ответов   |
| FastAPI          | —            | REST API для агентов на Python          |
| Docker Compose   | —            | Оркестрация контейнеров                 |

---

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Dev66-66/LAB13
cd LAB13

# 2. Настроить переменные окружения
cp .env.example .env
# Открыть .env и заполнить GEMINI_API_KEY своим ключом

# 3. Собрать и запустить все сервисы
docker compose up --build -d

# 4. Проверить работоспособность оркестратора
curl http://localhost:8000/health

# 5. Открыть панель мониторинга
#    http://localhost:8080

# 6. Открыть Jaeger UI для трассировки
#    http://localhost:16686
```

---

## Пример использования API

**Отправить юридический вопрос:**

```bash
curl -X POST http://localhost:8000/consult \
  -H "Content-Type: application/json" \
  -d '{"query": "Меня незаконно уволили, что делать?"}'
```

**Пример ответа:**

```json
{
  "task_id": "3f7a1b2c-...",
  "agent_id": "contradiction-checker-a1b2c3d4",
  "agent_role": "Проверщик противоречий",
  "success": true,
  "output": "{\"contradictions_found\": false, \"quality_score\": 90, \"notes\": \"...\"}",
  "duration_ms": 1842
}
```

**Получить список агентов и их статусы:**

```bash
curl http://localhost:8000/agents
```

**Просмотреть метрики системы:**

```bash
curl http://localhost:8000/metrics
```

**Демонстрация аукциона:**

```bash
curl http://localhost:8000/auction/demo
```

---

## Переменные окружения

| Переменная          | Описание                                                       |
|---------------------|----------------------------------------------------------------|
| `GEMINI_API_KEY`    | API-ключ Google Gemini для генерации текста                   |
| `NATS_URL`          | URL подключения к брокеру сообщений NATS                      |
| `REDIS_URL`         | URL подключения к Redis для кэширования сессий                |
| `JAEGER_ENDPOINT`   | Эндпоинт Jaeger для отправки трасс                            |
| `MAX_QUEUE_LENGTH`  | Максимальная длина очереди задач у агента до масштабирования  |
| `SCALE_THRESHOLD`   | Порог задач в очереди, при котором запускается новый экземпляр |
| `LOG_LEVEL`         | Уровень логирования (`DEBUG`, `INFO`, `WARN`, `ERROR`)        |
| `ORCHESTRATOR_PORT` | Порт HTTP API оркестратора                                    |
| `MONITORING_PORT`   | Порт панели мониторинга                                       |
| `AGENT_TIMEOUT_SEC` | Таймаут выполнения задачи агентом (в секундах)                |

---

## Демонстрация балансировки нагрузки

В `docker-compose.yml` запущены **два экземпляра** `query-analyzer` (`query-analyzer` и `query-analyzer-2`).
Оба подписаны на один NATS-топик `legal.query.raw`.
NATS автоматически распределяет входящие сообщения **round-robin** между всеми подписчиками одного топика — без дополнительной конфигурации.

Как проверить:

```bash
docker compose logs -f query-analyzer query-analyzer-2
```

При нагрузке в логах будет видно, что задачи чередуются между двумя контейнерами.
Динамически запущенные через `DynamicScaler` контейнеры также подписываются на тот же топик и автоматически включаются в балансировку.

---

## Структура проекта

```
LAB13/
├── agents/
│   ├── universal-agent/        # Go-агент (query-analyzer, document-searcher, contradiction-checker)
│   │   ├── configs/            # Конфигурационные промпты агентов
│   │   │   ├── query-analyzer.md
│   │   │   ├── document-searcher.md
│   │   │   ├── answer-generator.md
│   │   │   └── contradiction-checker.md
│   │   ├── internal/
│   │   │   ├── agent/          # agent.go, processor.go, processor_test.go
│   │   │   ├── config/         # loader.go
│   │   │   ├── models/         # task.go
│   │   │   └── tracing/        # tracer.go
│   │   ├── Dockerfile
│   │   └── main.go
│   └── answer-generator/       # Python-агент (Gemini API)
│       ├── agent.py
│       ├── gemini_client.py
│       ├── tracer.py
│       ├── main.py
│       └── Dockerfile
├── orchestrator/               # Оркестратор: маршрутизация, аукцион, масштабирование
│   ├── tests/                  # pytest: test_auction.py
│   ├── api.py
│   ├── auction.py
│   ├── orchestrator.py
│   ├── pipeline.py
│   ├── scaler.py
│   └── Dockerfile
├── monitoring/                 # Веб-дашборд (FastAPI + Jinja2 + dark CSS)
├── docs/                       # Архитектурная документация
│   └── ARCHITECTURE.md         # Mermaid pipeline, NATS topics, Redis keys, auction
├── docker/                     # Вспомогательные Docker-конфиги
├── docker-compose.yml          # 10 сервисов
├── .env.example                # Шаблон переменных окружения
├── .gitignore
├── README.md
└── PROMPT_LOG.md               # Журнал выполненных промптов
```
