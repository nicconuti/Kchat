import logging
from pathlib import Path
import sys
from pythonjsonlogger import jsonlogger

EXTRA_FIELDS = (
    "confidence_score",
    "source_reliability",
    "clarification_attempted",
    "error_flag",
)


class _ContextFilter(logging.Filter):
    """Ensure default values for custom log record fields."""

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        for field in EXTRA_FIELDS:
            if not hasattr(record, field):
                setattr(record, field, "")
        return True

YELLOW = "\x1b[33m"
WHITE = "\x1b[37m"
RESET = "\x1b[0m"


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes to logs/<name>.log."""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / f"{name}.log")
    file_fmt = (
        "%(asctime)s - %(message)s - "
        "confidence=%(confidence_score)s "
        "reliability=%(source_reliability)s "
        "clarification=%(clarification_attempted)s "
        "error=%(error_flag)s"
    )
    file_handler.setFormatter(logging.Formatter(file_fmt))
    file_handler.addFilter(_ContextFilter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(f"{YELLOW}[%(name)s]{WHITE} %(message)s{RESET}")
    )
    console_handler.addFilter(_ContextFilter())
    logger.addHandler(console_handler)
    return logger


def get_json_logger(name: str) -> logging.Logger:
    """Return logger writing JSON lines to logs/<name>.json."""
    logger = logging.getLogger(f"{name}_json")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_dir / f"{name}.json")
    handler.setFormatter(jsonlogger.JsonFormatter())
    handler.addFilter(_ContextFilter())
    logger.addHandler(handler)
    return logger
