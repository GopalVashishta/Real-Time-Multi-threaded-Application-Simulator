import threading
from utils import ThreadState
import time
import random
class Semaphore:
    def __init__(self, count=1, queue=None):
        self.count = count
        self.lock = threading.Lock()
        self.queue = []
        self.msg_queue = queue
        self.sem_id = id(self)
        if self.msg_queue:
            self.msg_queue.put({
                "type": "semaphore_created",
                "sem_id": self.sem_id,
                "count": self.count
            })

    def wait(self, thread):
        thread.set_state(ThreadState.READY)
        time.sleep(1)
        with self.lock:
            if self.count > 0:
                self.count -= 1
                thread.set_state(ThreadState.RUNNING)
                if self.msg_queue:
                    self.msg_queue.put({
                        "type": "semaphore_wait",
                        "thread_id": thread.thread_id,
                        "sem_id": self.sem_id,
                        "success": True
                    })
            else:
                thread.set_state(ThreadState.BLOCKED)
                self.queue.append(thread)
                if self.msg_queue:
                    self.msg_queue.put({
                        "type": "semaphore_wait",
                        "thread_id": thread.thread_id,
                        "sem_id": self.sem_id,
                        "success": False
                    })

    def signal(self):

        with self.lock:
            if self.queue:
                thread = self.queue.pop(0)
                thread.set_state(ThreadState.TERMINATED)
                time.sleep(random.randint(0,2))
                if self.msg_queue:
                    self.msg_queue.put({
                        "type": "semaphore_signal",
                        "sem_id": self.sem_id,
                        "thread_id": thread.thread_id
                    })
            else:
                self.count += 1
                if self.msg_queue:
                    self.msg_queue.put({
                        "type": "semaphore_signal",
                        "sem_id": self.sem_id,
                        "thread_id": None
                    })
                    

class Monitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.waiting_queue = []

    def enter(self, thread):
        thread.state = ThreadState.READY
        time.sleep(1)
        with self.lock:
            if thread.state == ThreadState.BLOCKED:
                time.sleep(2)
                self.waiting_queue.append(thread)
                self.condition.wait()
            thread.state = ThreadState.RUNNING
            #thread.run_task()
            print(f"Thread {thread.thread_id} is now RUNNING inside the monitor.")

    def exit(self,thread):
        with self.lock:
            if self.waiting_queue:
                next_thread = self.waiting_queue.pop(0)
                next_thread.state = ThreadState.BLOCKED
                self.condition.notify()
                print(f"Thread {thread.thread_id} is leaving the monitor.")
        

'''import threading
from utils import ThreadState

class Semaphore:
    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Lock()
        self.queue = []

    def wait(self, thread):
        """Acquire the semaphore."""
        with self.lock:
            if self.count > 0:
                self.count -= 1
                thread.state = ThreadState.RUNNING
                print(f"\tThread {thread.thread_id} is now RUNNING.")
            else:
                thread.state = ThreadState.BLOCKED
                self.queue.append(thread)
                print(f"\tThread {thread.thread_id} is BLOCKED and waiting.")

    def signal(self):
        """Release the semaphore."""
        with self.lock:
            if self.queue:
                thread = self.queue.pop(0)
                thread.state = ThreadState.READY
                print(f"\tThread {thread.thread_id} moved to READY state.")
            else:
                self.count += 1


class Monitor:
    def __init__(self):
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.waiting_queue = []  # Keep track of waiting threads

    def enter(self, thread):
        """Enter the monitor, blocking if necessary."""
        with self.lock:
            if thread.state == ThreadState.BLOCKED:
                self.waiting_queue.append(thread)
                print(f"Thread {thread.thread_id} is BLOCKED and waiting.")
                self.condition.wait()
            
            thread.state = ThreadState.RUNNING
            thread.run_task()
            print(f"Thread {thread.thread_id} is now RUNNING inside the monitor.")

    def exit(self, thread):
        """Exit the monitor, waking up a waiting thread if present."""
        with self.lock:
            if self.waiting_queue:
                next_thread = self.waiting_queue.pop(0)
                next_thread.state = ThreadState.READY
                print(f"Thread {next_thread.thread_id} moved to READY state.")
                self.condition.notify()
            
            thread.state = ThreadState.READY
            print(f"Thread {thread.thread_id} is leaving the monitor.")
'''
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
'''
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
'''
