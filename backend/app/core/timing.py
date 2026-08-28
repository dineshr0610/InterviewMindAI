"""
Simple timing utilities for measuring operation latency.
"""

import time
import logging

logger = logging.getLogger("interviewmind.timing")


class TimingContext:
    """Context manager for measuring operation timing."""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.elapsed_ms = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        status = "error" if exc_type else "ok"
        logger.info(
            f"[timing] {self.operation_name} {status}: {self.elapsed_ms:.0f}ms"
        )
        return False


def log_timing(operation_name: str, elapsed_ms: float):
    """Log a timing measurement."""
    logger.info(f"[timing] {operation_name}: {elapsed_ms:.0f}ms")
