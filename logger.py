"""File logging for Speakboard. Writes speakboard.log next to main.py."""

import logging
import sys
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "speakboard.log"
_MAX_BYTES = 512 * 1024  # rotate when log exceeds 512 KB

_logger: logging.Logger | None = None


def _rotate_if_needed() -> None:
    if LOG_PATH.exists() and LOG_PATH.stat().st_size > _MAX_BYTES:
        backup = LOG_PATH.with_suffix(".log.old")
        backup.unlink(missing_ok=True)
        LOG_PATH.replace(backup)


def setup_logging() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    _rotate_if_needed()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("speakboard")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    if sys.stdout is not None:
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(fmt)
        logger.addHandler(stream)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    return _logger or setup_logging()


def log_startup_banner() -> None:
    log = get_logger()
    log.info("=" * 60)
    log.info("Speakboard starting")
    log.info("executable=%s", sys.executable)
    log.info("argv=%s", sys.argv)
    log.info("log_file=%s", LOG_PATH)


def log_fatal(exc: BaseException) -> None:
    log = get_logger()
    log.exception("Fatal error: %s", exc)
