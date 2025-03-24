# __init__.py
"""
Multi-threaded Application Simulator Package

Modules:
- models.py: Implements different multithreading models.
- synchronization.py: Provides Semaphore and Monitor for synchronization.
- utils.py: Provides helper functions like thread-safe logging.
"""

# Import necessary components for easy access
from .models import many_to_one, one_to_many, many_to_many
from .synchronization import Semaphore, Monitor
from .utils import log_message
