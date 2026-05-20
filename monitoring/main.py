from dotenv import load_dotenv
load_dotenv()

import logging
import os
import sys

import uvicorn
from app import app

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
