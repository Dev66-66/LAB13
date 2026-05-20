import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import nats
import redis as redis_lib

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Управляет отправкой задач агентам через NATS и ожиданием их результатов."""

    def __init__(self) -> None:
        self.nc: nats.NATS | None = None
        self.rdb: redis_lib.Redis | None = None
        self.pending_tasks: dict[str, asyncio.Future] = {}

    async def connect(self) -> None:
        """Подключается к NATS и Redis, подписывается на выходные топики всех агентов."""
        self.nc = await nats.connect(os.getenv("NATS_URL", "nats://nats:4222"))
        self.rdb = redis_lib.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
        # Подписываемся на все выходные топики, чтобы отслеживать результаты каждого шага
        for topic in (
            "legal.query.analyzed",
            "legal.docs.found",
            "legal.answer.raw",
            "legal.answer.final",
        ):
            await self.nc.subscribe(topic, cb=self._on_result)
        logger.info("Orchestrator connected to NATS and Redis")

    async def send_task(
        self, task_type: str, payload: dict, topic: str, timeout: int = 30
    ) -> dict:
        """
        Создаёт задачу, публикует в NATS-топик и ожидает результата.
        Бросает asyncio.TimeoutError если агент не ответил за timeout секунд.
        """
        task = {
            "id": str(uuid4()),
            "type": task_type,
            "payload": json.dumps(payload),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": "",
            "span_id": "",
            "pipeline": [],
            "current_step": 0,
            "metadata": {},
        }
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self.pending_tasks[task["id"]] = future

        await self.nc.publish(topic, json.dumps(task).encode())

        try:
            result_raw = await asyncio.wait_for(future, timeout=timeout)
            return json.loads(result_raw)
        except asyncio.TimeoutError:
            self.pending_tasks.pop(task["id"], None)
            raise

    async def _on_result(self, msg) -> None:
        """Разрешает ожидающий Future по task_id из входящего сообщения."""
        try:
            result = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        task_id = result.get("task_id")
        if task_id and task_id in self.pending_tasks:
            future = self.pending_tasks.pop(task_id)
            if not future.done():
                future.set_result(msg.data.decode())
