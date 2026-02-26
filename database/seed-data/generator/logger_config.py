"""
Structured logging configuration for VelocityBench generators.

Provides consistent logging across all generator scripts with support for:
- Console output with color-coded levels
- File logging for audit trails
- Structured JSON logging for parsing
- Environment-based log level control
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path


def setup_logging(
    name: str,
    log_dir: Path | None = None,
    level: str | None = None,
) -> logging.Logger:
    """
    Set up structured logging for a generator script.

    Args:
        name: Logger name (typically __name__)
        log_dir: Directory for log files (default: $PWD/logs)
        level: Log level (DEBUG, INFO, WARNING, ERROR) - overrides env var

    Returns:
        Configured logger instance

    Environment Variables:
        LOGLEVEL: Set log level (DEBUG, INFO, WARNING, ERROR)
        LOG_DIR: Override log directory
    """
    # Get log level from environment or parameter
    if level is None:
        level = os.environ.get("LOGLEVEL", "INFO").upper()

    # Get log directory
    if log_dir is None:
        log_dir = Path(os.environ.get("LOG_DIR", "logs"))
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (DEBUG and above)
    script_name = Path(name).stem if "/" in name else name.split(".")[-1]
    log_file = log_dir / f"{script_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Suppress verbose third-party logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return logger


# Module-level convenience functions for quick setup
_default_logger: logging.Logger | None = None


def get_logger(name: str = "velocitybench") -> logging.Logger:
    """Get or create default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging(name)
    return _default_logger


def info(msg: str, *args, **kwargs) -> None:
    """Log info message."""
    get_logger().info(msg, *args, **kwargs)


def debug(msg: str, *args, **kwargs) -> None:
    """Log debug message."""
    get_logger().debug(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """Log warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """Log error message."""
    get_logger().error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    """Log exception with traceback."""
    get_logger().exception(msg, *args, **kwargs)
