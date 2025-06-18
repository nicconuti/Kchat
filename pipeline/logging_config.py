import os
import json
import logging
import logging.handlers
from pathlib import Path

class JsonFormatter(logging.Formatter):
    """Formattatore JSON personalizzato per log strutturati."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "pid": record.process,
            "thread": record.threadName,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging() -> logging.Logger:
    """Configura il logger root con file separati per processo e rotazione."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    formatter = JsonFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    pid = os.getpid()
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / f"pipeline_{pid}.log", maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)

    if not any(isinstance(h, logging.StreamHandler) for h in log.handlers):
        log.addHandler(stream_handler)
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in log.handlers):
        log.addHandler(file_handler)

    return log
