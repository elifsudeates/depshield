"""
Logging utilities for DepShield
================================

This module provides logging functionality with timestamps and log levels.
Used throughout the application for debugging and status reporting.

Author: Elif Sude ATES
GitHub: https://github.com/elifsudeates/depshield
"""

from datetime import datetime


def log(message: str, level: str = "INFO") -> None:
    """
    Print a log message with timestamp and log level.
    
    This function outputs formatted log messages to stdout with millisecond
    precision timestamps. Messages are flushed immediately for real-time
    logging during long operations.
    
    Args:
        message: The message to log
        level: Log level (INFO, WARN, ERROR, DEBUG)
    
    Example:
        >>> log("Starting scan...", "INFO")
        [14:32:15.123] [INFO] Starting scan...
        
        >>> log("File not found", "WARN")
        [14:32:15.456] [WARN] File not found
    """
    # Format timestamp with milliseconds for precise timing
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Print formatted message and flush immediately
    # flush=True ensures real-time output during streaming
    print(f"[{timestamp}] [{level}] {message}", flush=True)


def log_info(message: str) -> None:
    """Log an informational message."""
    log(message, "INFO")


def log_warn(message: str) -> None:
    """Log a warning message."""
    log(message, "WARN")


def log_error(message: str) -> None:
    """Log an error message."""
    log(message, "ERROR")


def log_debug(message: str) -> None:
    """Log a debug message."""
    log(message, "DEBUG")


def log_success(message: str) -> None:
    """Log a success message with checkmark."""
    log(f"✓ {message}", "INFO")


def log_failure(message: str) -> None:
    """Log a failure message with X mark."""
    log(f"✗ {message}", "ERROR")
