from dotenv import load_dotenv
load_dotenv()

import asyncio  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

import redis  # noqa: E402

from agent import AnswerGeneratorAgent  # noqa: E402
from gemini_client import GeminiClient  # noqa: E402
from tracer import init_tracer  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def main() -> None:
    init_tracer("answer-generator")

    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
    gemini_client = GeminiClient(os.getenv("GEMINI_API_KEY", ""))
    agent = AnswerGeneratorAgent(gemini_client, redis_client)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Получен сигнал завершения, останавливаем агент...")
        sys.exit(0)


if __name__ == "__main__":
    main()
