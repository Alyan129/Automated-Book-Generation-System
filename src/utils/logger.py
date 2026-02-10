"""
Logger configuration using loguru.
Provides structured logging with file rotation.
"""
import sys
from pathlib import Path
from loguru import logger
from src.core.config import config

# Remove default logger
logger.remove()

# Console logger with color
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=config.LOG_LEVEL,
    colorize=True
)

# File logger with rotation
log_dir = Path(__file__).parent.parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "book_generator_{time:YYYY-MM-DD}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)

# Export logger
__all__ = ['logger']
