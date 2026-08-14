from __future__ import annotations

import sys

from loguru import logger

from md5_rebuilder.utils.paths import data_home


def setup_logging() -> None:
    logger.remove()
    if sys.stderr is not None:
        logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    try:
        log_path = data_home() / "logs" / "app.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path,
            level="INFO",
            rotation="10 MB",
            retention="7 days",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )
    except OSError:
        if sys.stderr is None:
            logger.add(_discard, level="INFO")


def _discard(message) -> None:
    return None
