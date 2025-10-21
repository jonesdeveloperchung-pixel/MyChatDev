"""Logging configuration for the cooperative LLM system.

Author: Jones Chung
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Configure logging with timestamps and detailed formatting."""

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Set default log file if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"coop_llm_{timestamp}.log"

    # Configure logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    # Create logger
    logger = logging.getLogger("coop_llm")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def log_node_execution(
    logger: logging.Logger,
    node_name: str,
    input_data: dict,
    output_data: dict,
    execution_time: float,
):
    """Log detailed node execution information."""
    logger.info(f"=== NODE EXECUTION: {node_name} ===")
    logger.info(f"Execution time: {execution_time:.2f}s")
    logger.info(f"Input keys: {list(input_data.keys())}")
    logger.info(f"Output keys: {list(output_data.keys())}")

    # Log input/output sizes for debugging
    for key, value in input_data.items():
        if isinstance(value, str):
            logger.debug(f"Input {key}: {len(value)} characters")

    for key, value in output_data.items():
        if isinstance(value, str):
            logger.debug(f"Output {key}: {len(value)} characters")
