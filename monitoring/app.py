import os
from datetime import datetime, timezone
from pathlib import Path

import redis as redis_lib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from redis_client import MonitoringRedisClient

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Legal MAS Monitor")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
JAEGER_URL = os.getenv("JAEGER_URL", "http://localhost:16686")

rdb = redis_lib.from_url(REDIS_URL)
rc = MonitoringRedisClient(rdb)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "metrics": rc.get_system_metrics(),
        "agents": rc.get_all_agents(),
    })


@app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    return templates.TemplateResponse("agents.html", {
        "request": request,
        "agents": rc.get_all_agents(),
    })


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    tasks: list[dict] = []
    cursor = 0
    while True:
        cursor, keys = rdb.scan(cursor, match="answer:*", count=100)
        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            task_id = key_str.split(":", 1)[1] if ":" in key_str else key_str
            val = rdb.get(key)
            answer = val.decode() if val else ""
            tasks.append({
                "id": task_id,
                "preview": answer[:150] + "…" if len(answer) > 150 else answer,
            })
        if cursor == 0:
            break
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
    })


@app.get("/traces", response_class=HTMLResponse)
async def traces_page(request: Request):
    return templates.TemplateResponse("traces.html", {
        "request": request,
        "jaeger_url": JAEGER_URL,
    })


@app.get("/api/stats")
async def api_stats():
    """JSON-эндпоинт для JavaScript авторефреша без перезагрузки страницы."""
    metrics = rc.get_system_metrics()
    agents = rc.get_all_agents()
    return {
        "agents_online": metrics["online_agents"],
        "total_tasks_processed": metrics["total_tasks_processed"],
        "scaled_agents": metrics["scaled_agents"],
        "agents": agents,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
