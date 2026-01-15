import os
from pathlib import Path

from loguru import logger

from src.core.config import get_settings


def setup_logging() -> None:
    settings = get_settings()

    # Remove handlers default
    logger.remove()

    # Console
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level.upper(),
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # Arquivo (rotaciona)
    log_dir = Path(settings.log_dir)
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        str(log_dir / "app.log"),
        level=settings.log_level.upper(),
        rotation="10 MB",
        retention="10 days",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

