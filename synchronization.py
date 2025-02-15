import threading

class Semaphore:
    """Custom Semaphore Implementation"""
    def __init__(self, value=1):
        """Initialize semaphore with a given value (default = 1)."""
        self.sem = threading.Semaphore(value)

    def acquire(self):
        """Acquire the semaphore (wait operation)."""
        self.sem.acquire()

    def release(self):
        """Release the semaphore (signal operation)."""
        self.sem.release()

class Monitor:
    """Monitor with Lock and Condition Variable"""
    def __init__(self):
        """Initialize monitor with a lock and condition variable."""
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def wait(self):
        """Wait on condition variable (block until notified)."""
        with self.condition:
            self.condition.wait()

    def notify(self):
        """Notify all waiting threads."""
        with self.condition:
            self.condition.notify_all()
