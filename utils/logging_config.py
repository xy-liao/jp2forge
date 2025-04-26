"""
Logging configuration for JP2Forge.

This module provides utility functions for configuring logging
in a consistent manner throughout the application.
"""

import os
import logging
from typing import Optional


def configure_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    verbose: bool = False
) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (default: logging.INFO)
        log_file: Path to log file (default: None, log to console only)
        log_format: Logging format string
        verbose: Whether to enable verbose logging
    """
    # Set log level based on verbose flag
    if verbose:
        log_level = logging.DEBUG
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Set specific levels for noisy libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.debug("Logging configured")
    if log_file:
        logger.info(f"Logging to file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
