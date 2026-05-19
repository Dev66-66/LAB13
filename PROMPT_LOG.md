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
