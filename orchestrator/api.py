import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager

import redis as redis_lib
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auction import AuctionManager

logger = logging.getLogger(__name__)

_orchestrator = None
_pipeline = None
_redis_client: redis_lib.Redis | None = None
_startup_fn = None


def setup(orchestrator, pipeline, redis_client: redis_lib.Redis) -> None:
    """Внедряет зависимости из main.py."""
    global _orchestrator, _pipeline, _redis_client
    _orchestrator = orchestrator
    _pipeline = pipeline
    _redis_client = redis_client


def set_startup(fn) -> None:
    """Регистрирует async-функцию, которую нужно вызвать при старте приложения."""
    global _startup_fn
    _startup_fn = fn


@asynccontextmanager
async def _lifespan(app: FastAPI):
    if _startup_fn:
        await _startup_fn()
    yield


app = FastAPI(title="Legal MAS Orchestrator", lifespan=_lifespan)


@app.middleware("http")
async def _log_requests(request: Request, call_next):
    t0 = time.time()
    response = await call_next(request)
    logger.info(json.dumps({
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": int((time.time() - t0) * 1000),
    }))
    return response


class ConsultRequest(BaseModel):
    query: str


@app.post("/consult")
async def consult(body: ConsultRequest):
    """Запускает полный pipeline юридической консультации и возвращает итоговый результат."""
    result = await _pipeline.execute(body.query)
    return result


@app.get("/health")
async def health():
    """Проверяет связь с NATS и Redis, возвращает количество онлайн-агентов."""
    nats_ok = False
    redis_ok = False
    agents_online = 0
    try:
        nats_ok = _orchestrator.nc is not None and _orchestrator.nc.is_connected
    except Exception:
        pass
    try:
        _redis_client.ping()
        redis_ok = True
        cursor = 0
        while True:
            cursor, keys = _redis_client.scan(cursor, match="agent:*:status", count=100)
            agents_online += len(keys)
            if cursor == 0:
                break
    except Exception:
        pass
    return {"status": "ok", "nats": nats_ok, "redis": redis_ok, "agents_online": agents_online}


@app.get("/agents")
async def agents():
    """Возвращает список всех зарегистрированных агентов с их статусами."""
    result = []
    cursor = 0
    all_keys = []
    while True:
        cursor, keys = _redis_client.scan(cursor, match="agent:*:status", count=100)
        all_keys.extend(keys)
        if cursor == 0:
            break
    for key in all_keys:
        key_str = key.decode() if isinstance(key, bytes) else key
        parts = key_str.split(":")
        if len(parts) < 3:
            continue
        agent_id = ":".join(parts[1:-1])
        status_raw = _redis_client.get(key)
        status = status_raw.decode() if status_raw else "unknown"
        tasks_raw = _redis_client.get(f"agent:{agent_id}:tasks_processed")
        tasks = int(tasks_raw) if tasks_raw else 0
        result.append({"id": agent_id, "status": status, "tasks_processed": tasks})
    return result


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Возвращает кэшированный ответ по task_id или 404."""
    answer = _redis_client.get(f"answer:{task_id}")
    if answer is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "answer": answer.decode() if isinstance(answer, bytes) else answer}


@app.get("/metrics")
async def metrics():
    """Агрегирует суммарное количество обработанных задач по всем агентам."""
    total_tasks = 0
    agents_online = 0
    cursor = 0
    while True:
        cursor, keys = _redis_client.scan(cursor, match="agent:*:tasks_processed", count=100)
        for key in keys:
            val = _redis_client.get(key)
            if val:
                total_tasks += int(val)
        if cursor == 0:
            break
    cursor = 0
    while True:
        cursor, keys = _redis_client.scan(cursor, match="agent:*:status", count=100)
        agents_online += len(keys)
        if cursor == 0:
            break
    return {"total_tasks": total_tasks, "agents_online": agents_online}


@app.get("/auction/demo")
async def auction_demo():
    """Демонстрирует аукционное распределение: возвращает ставки агентов и победителя."""
    manager = AuctionManager()
    bids = manager.get_agent_bids(_redis_client)
    winner = manager.select_winner(bids)
    return {
        "participants": [
            {"agent_id": b.agent_id, "role": b.role, "bid": b.bid, "status": b.status}
            for b in bids
        ],
        "winner": (
            {"agent_id": winner.agent_id, "role": winner.role, "bid": winner.bid}
            if winner
            else None
        ),
    }
