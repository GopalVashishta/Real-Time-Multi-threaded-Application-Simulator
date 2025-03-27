"""
Thread Simulator - Logging Module
This module provides centralized logging functionality for the thread simulator.
"""

import logging
import sys
import os
import traceback
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure the logger
log_file = os.path.join(log_dir, f'thread_simulator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'

# Create and configure logger
logger = logging.getLogger('thread_simulator')
logger.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(console_handler)

def log_exception(e, additional_info=""):
    """
    Log an exception with its full traceback and additional context information.
    """
    error_message = f"{additional_info} Exception: {str(e)}"
    logger.error(error_message)
    logger.error(traceback.format_exc())
    return error_message

def log_debug(message):
    """Log a debug message."""
    logger.debug(message)

def log_info(message):
    """Log an info message."""
    logger.info(message)

def log_warning(message):
    """Log a warning message."""
    logger.warning(message)

def log_error(message):
    """Log an error message."""
    logger.error(message)
