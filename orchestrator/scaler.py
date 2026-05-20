import logging
import os

import docker
import httpx

logger = logging.getLogger(__name__)

_NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
_JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", "http://jaeger:14268/api/traces")


class DynamicScaler:
    """Динамически масштабирует агентов на основе глубины очереди NATS."""

    SCALE_THRESHOLD = int(os.getenv("SCALE_THRESHOLD", "3"))

    async def check_and_scale(self, rdb) -> None:
        """
        Проверяет нагрузку через NATS HTTP API.
        Запускает новый контейнер агента при превышении порога,
        останавливает лишний при пустой очереди.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://nats:8222/subsz")
                data = response.json()
        except Exception as exc:
            logger.warning("Не удалось получить метрики NATS: %s", exc)
            return

        total_pending = data.get("total_pending", data.get("num_subscriptions", 0))

        if total_pending > self.SCALE_THRESHOLD:
            try:
                def _run_container():
                    return docker.from_env().containers.run(
                        image="lab13-universal-agent",
                        detach=True,
                        environment={
                            "AGENT_CONFIG": "/app/configs/query-analyzer.md",
                            "NATS_URL": _NATS_URL,
                            "REDIS_URL": _REDIS_URL,
                            "JAEGER_ENDPOINT": _JAEGER_ENDPOINT,
                        },
                        network="lab13_legal-mas-network",
                        remove=False,
                    )
                container = await asyncio.to_thread(_run_container)
                rdb.sadd("scaled_agents", container.id)
                print(f"[Scaler] Запущен новый агент: {container.id[:12]}")
            except Exception as exc:
                logger.error("Не удалось запустить контейнер: %s", exc)

        elif total_pending == 0 and rdb.scard("scaled_agents") > 0:
            try:
                cid_raw = rdb.spop("scaled_agents")
                cid = cid_raw.decode() if isinstance(cid_raw, bytes) else cid_raw
                await asyncio.to_thread(lambda: docker.from_env().containers.get(cid).stop())
                print(f"[Scaler] Остановлен лишний агент: {cid[:12]}")
            except Exception as exc:
                logger.error("Не удалось остановить контейнер: %s", exc)
