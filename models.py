import threading
import time
import random
from synchronization import Semaphore

# === Many-to-One Model === #
def many_to_one(num_threads):
    """Simulates Many-to-One model: Multiple threads sharing a single scheduler."""
    scheduler = Semaphore(1)  # Only 1 thread can run at a time
    threads = []


    for i in range(num_threads):
        t = threading.Thread(target=many_to_one_worker, args=(i, scheduler))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


def many_to_one_worker(thread_id, scheduler):
    """Worker function for Many-to-One model."""
    scheduler.acquire()
    time.sleep(random.uniform(0.5, 1.5))
    scheduler.release()

# === One-to-Many Model === #
def one_to_many(num_threads):
    """Simulates One-to-Many model: A single thread dispatching multiple worker threads."""

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=one_to_many_worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


def one_to_many_worker(thread_id):
    """Worker function for One-to-Many model."""
    time.sleep(random.uniform(0.5, 1.5))

# === Many-to-Many Model === #
def many_to_many(num_threads):
    """Simulates Many-to-Many model: Multiple threads working with multiple schedulers."""
    scheduler_count = min(num_threads, 3)  # Allow up to 3 schedulers
    schedulers = [Semaphore(1) for _ in range(scheduler_count)]


    threads = []
    for i in range(num_threads):
        scheduler = schedulers[i % scheduler_count]  # Assign thread to a scheduler
        t = threading.Thread(target=many_to_many_worker, args=(i, scheduler))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()


def many_to_many_worker(thread_id, scheduler):
    """Worker function for Many-to-Many model."""
    scheduler.acquire()
    time.sleep(random.uniform(0.5, 1.5))
    scheduler.release()
