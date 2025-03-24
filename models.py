import threading
import time
import random
from synchronization import Semaphore
from utils import log_message

# === Many-to-One Model === #
def many_to_one(num_threads, sem_val):
    """Simulates Many-to-One model: Multiple threads sharing a single scheduler."""
    scheduler = Semaphore(sem_val)  # initializing the value of semaphore(user-given)
    threads = []

    log_message(f"\n[Many-to-One] Starting with {num_threads} threads")

    for i in range(num_threads):
        t = threading.Thread(target=many_to_one_worker, args=(i, scheduler))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    log_message("[Many-to-One] Completed.\n")

def many_to_one_worker(thread_id, scheduler):
    """Worker function for Many-to-One model."""
    scheduler.acquire()
    log_message(f"[Thread {thread_id}] Running on single scheduler")
    time.sleep(random.uniform(0.5, 1.5))
    scheduler.release()

# === One-to-Many Model === #
def one_to_many(num_threads):
    """Simulates One-to-Many model: A single thread dispatching multiple worker threads."""
    log_message(f"\n[One-to-Many] Dispatching {num_threads} threads")

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=one_to_many_worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    log_message("[One-to-Many] Completed.\n")

def one_to_many_worker(thread_id):
    """Worker function for One-to-Many model."""
    log_message(f"[Thread {thread_id}] Running independently")
    time.sleep(random.uniform(0.5, 1.5))

# === Many-to-Many Model === #
def many_to_many(num_threads):
    """Simulates Many-to-Many model: Multiple threads working with multiple schedulers."""
    scheduler_count = min(num_threads, 3)  # Allow up to 3 schedulers
    schedulers = [Semaphore(1) for _ in range(scheduler_count)]

    log_message(f"\n[Many-to-Many] Running with {num_threads} threads and {scheduler_count} schedulers")

    threads = []
    for i in range(num_threads):
        scheduler = schedulers[i % scheduler_count]  # Assign thread to a scheduler
        t = threading.Thread(target=many_to_many_worker, args=(i, scheduler))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    log_message("[Many-to-Many] Completed.\n")

def many_to_many_worker(thread_id, scheduler):
    """Worker function for Many-to-Many model."""
    scheduler.acquire()
    log_message(f"[Thread {thread_id}] Running on a shared scheduler")
    time.sleep(random.uniform(0.5, 1.5))
    scheduler.release()
