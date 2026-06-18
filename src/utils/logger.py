"""
Centralized logging configuration for GRIDLOCK.

Uses loguru for structured, colorized logging with file rotation.
All modules should import `logger` from this module.
"""

import sys
from pathlib import Path

from loguru import logger

# ─── Remove default handler ──────────────────────────────────
logger.remove()

# ─── Console handler (colorized, human-readable) ─────────────
logger.add(
    sys.stderr,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# ─── File handler (JSON, rotated daily, 30-day retention) ────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.add(
    LOG_DIR / "gridlock_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    rotation="00:00",  # Rotate at midnight
    retention="30 days",
    compression="gz",
    serialize=False,
)

# ─── Structured JSON log for machine parsing ─────────────────
logger.add(
    LOG_DIR / "gridlock_structured_{time:YYYY-MM-DD}.jsonl",
    level="INFO",
    serialize=True,  # Outputs JSON lines
    rotation="00:00",
    retention="14 days",
    compression="gz",
)


def get_logger(name: str):
    """Get a contextualized logger for a specific module.

    Args:
        name: Module or component name for log context.

    Returns:
        Bound logger instance with the given name context.
    """
    return logger.bind(component=name)
