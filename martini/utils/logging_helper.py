# logging_helper.py

import logging
from logging.handlers import RotatingFileHandler
import os
import time

# Constants for log file and level
LOG_FILE = 'logs/main.log'
LOG_LEVEL = logging.INFO
LOGGER_NAME = "main"

def setup_logging() -> logging.Logger:
    """
    Sets up logging to file and console with consistent formatting.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    # Clear any existing handlers
    logging.getLogger().handlers = []

    # Create the logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(LOG_LEVEL)

    # Define the ISO8601 formatter for both file and stream logs
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(module)s]: %(message)s', 
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )

    # Use UTC time for logs
    logging.Formatter.converter = time.gmtime  # Ensure UTC time

    # Rotating File Handler (for log file output)
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=10**7,  # 10 MB per file
        backupCount=5,   # Keep up to 5 backup files
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    # Stream handler (for console output)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(LOG_LEVEL)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


# Initialize logger with the default settings
logger = setup_logging()

def set_log_level_to_debug():
    """
    Sets the log level to DEBUG.
    """
    _logger = logging.getLogger(LOGGER_NAME)
    _logger.setLevel(logging.DEBUG)


def set_log_level_to_info():
    """
    Sets the log level to INFO.
    """
    _logger = logging.getLogger(LOGGER_NAME)
    _logger.setLevel(logging.INFO)
