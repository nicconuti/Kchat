import logging
from pathlib import Path
import sys

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
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(f"{YELLOW}[%(name)s]{WHITE} %(message)s{RESET}")
    )
    logger.addHandler(console_handler)
    return logger
