"""
Structured logging configuration for Superstore Data Pipeline.
Outputs cleanly formatted log messages to console and file.
"""

import logging
import sys
from pathlib import Path
from config.config import config


def get_logger(name: str = "superstore_pipeline") -> logging.Logger:
    """Configures and returns a standard logger instance."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    level = getattr(logging, config.log_level, logging.INFO)
    logger.setLevel(level)

    # Format: 2026-10-06 10:00:00 INFO Message
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        config.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            config.paths.logs_dir / "pipeline.log",
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not create file handler for logs: {e}\n")

    return logger
