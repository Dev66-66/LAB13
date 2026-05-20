from dotenv import load_dotenv
load_dotenv()

import logging  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

import uvicorn  # noqa: E402
from app import app  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def main() -> None:
    port = int(os.getenv("MONITORING_PORT", "8080"))
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Мониторинг остановлен.")
        sys.exit(0)


if __name__ == "__main__":
    main()
