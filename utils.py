import threading

# Lock to ensure thread-safe console output
console_lock = threading.Lock()

def log_message(message):
    """Thread-safe print function to prevent overlapping output."""
    with console_lock:
        print(message)
