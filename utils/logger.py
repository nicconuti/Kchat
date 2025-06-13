import logging
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes to logs/<name>.log."""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_dir / f"{name}.log")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(handler)
    return logger
