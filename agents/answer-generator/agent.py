import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import nats
import redis as redis_lib
from opentelemetry import trace

from gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class AnswerGeneratorAgent:
    """Агент генерации юридических ответов через Gemini API."""

    AGENT_ID = "answer-generator-" + uuid4().hex[:8]

    def __init__(self, gemini_client: GeminiClient, redis_client: redis_lib.Redis) -> None:
        self.gemini_client = gemini_client
        self.redis_client = redis_client
        self._status = "idle"
        self._nc: nats.NATS | None = None

    async def start(self) -> None:
        """Подключается к NATS, подписывается на топик и блокируется до завершения."""
        nc = await nats.connect(os.getenv("NATS_URL", "nats://nats:4222"))
        self._nc = nc
        await nc.subscribe("legal.docs.found", cb=self._handle_message)
        self.redis_client.set(f"agent:{self.AGENT_ID}:status", "idle", ex=60)
        asyncio.create_task(self._keepalive(nc))
        await asyncio.Event().wait()

    async def _handle_message(self, msg) -> None:
        """Обрабатывает задачу: вызывает Gemini API, кэширует ответ, публикует результат."""
        tracer = trace.get_tracer("answer-generator")
        with tracer.start_as_current_span("answer_generator.process_task") as span:
            try:
                task = json.loads(msg.data)
                span.set_attribute("task.id", task.get("id", ""))
                span.set_attribute("agent.id", self.AGENT_ID)

                payload_data = json.loads(task.get("payload", "{}"))
                query = payload_data.get("original_query", "")
                documents = payload_data.get("documents", [])

                self._status = "busy"
                self.redis_client.set(f"agent:{self.AGENT_ID}:status", "busy", ex=60)

                t0 = asyncio.get_event_loop().time()
                answer = await self.gemini_client.generate_legal_answer(query, documents)
                duration_ms = int((asyncio.get_event_loop().time() - t0) * 1000)

                self.redis_client.set(f"answer:{task['id']}", answer, ex=600)
                self.redis_client.incr(f"agent:{self.AGENT_ID}:tasks_processed")

                result = {
                    "task_id": task["id"],
                    "agent_id": self.AGENT_ID,
                    "agent_role": "Генератор юридических ответов",
                    "success": True,
                    "output": answer,
                    "trace_id": task.get("trace_id", ""),
                    "duration_ms": duration_ms,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
                await self._nc.publish("legal.answer.raw", json.dumps(result).encode())

                self._status = "idle"
                self.redis_client.set(f"agent:{self.AGENT_ID}:status", "idle", ex=60)

                self._write_log(task.get("id", ""), duration_ms)

            except Exception as exc:
                span.record_exception(exc)
                logger.error("Error processing message: %s", exc)
                self._status = "idle"

    async def _keepalive(self, nc) -> None:
        """Обновляет TTL статуса агента в Redis каждые 30 секунд."""
        while True:
            await asyncio.sleep(30)
            self.redis_client.set(f"agent:{self.AGENT_ID}:status", self._status, ex=60)

    def _write_log(self, task_id: str, duration_ms: int) -> None:
        os.makedirs("logs", exist_ok=True)
        entry = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "agent_id": self.AGENT_ID,
            "agent_role": "Генератор юридических ответов",
            "task_id": task_id,
            "duration_ms": duration_ms,
            "message": "task processed",
        })
        with open("logs/answer-generator.log", "a", encoding="utf-8") as f:
            f.write(entry + "\n")
