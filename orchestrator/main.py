from dotenv import load_dotenv
load_dotenv()

import asyncio  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

import redis  # noqa: E402
import uvicorn  # noqa: E402

import api  # noqa: E402
from orchestrator import AgentOrchestrator  # noqa: E402
from pipeline import LegalPipeline  # noqa: E402
from scaler import DynamicScaler  # noqa: E402
from tracer import init_tracer  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "8000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

_rdb = redis.from_url(REDIS_URL)
_orchestrator = AgentOrchestrator()
_pipeline = LegalPipeline(_orchestrator)
_scaler = DynamicScaler()

api.setup(_orchestrator, _pipeline, _rdb)


async def _scaler_loop() -> None:
    while True:
        await asyncio.sleep(10)
        try:
            await _scaler.check_and_scale(_rdb)
        except Exception as exc:
            logger.error("Scaler error: %s", exc)


async def _startup() -> None:
    await _orchestrator.connect()
    asyncio.create_task(_scaler_loop())
    logger.info("Orchestrator started on port %d", ORCHESTRATOR_PORT)


api.set_startup(_startup)


def main() -> None:
    init_tracer("orchestrator")
    try:
        uvicorn.run(api.app, host="0.0.0.0", port=ORCHESTRATOR_PORT)
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения, останавливаем оркестратор...")
        sys.exit(0)


if __name__ == "__main__":
    main()
