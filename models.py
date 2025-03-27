"""
Thread Simulator - Core Models
This module contains the core models for the thread simulator including Thread, Process, and ThreadingModel.
"""

import time
import threading
import enum
from typing import List, Dict, Callable, Any

# Thread States
class ThreadState(enum.Enum):
    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    BLOCKED = "Blocked"
    TERMINATED = "Terminated"

# Thread Model Types
class ThreadModelType(enum.Enum):
    MANY_TO_ONE = "Many-to-One"
    ONE_TO_MANY = "One-to-Many"
    MANY_TO_MANY = "Many-to-Many"
    ONE_TO_ONE = "One-to-One"

class Thread:
    """Represents a user thread in the system"""
    
    next_id = 1
    
    def __init__(self, name=None, function=None, args=None):
        self.id = Thread.next_id
        Thread.next_id += 1
        self.name = name or f"Thread-{self.id}"
        self.state = ThreadState.NEW
        self.function = function or self._default_function
        self.args = args or []
        self.execution_time = 0
        self.start_time = None
        self.end_time = None
        self.kernel_thread = None
        self.progress = 0  # Progress from 0-100%
        self.blocked_by = None  # Reference to blocking resource
        self.history = []  # Track state transitions
        
        # Add initial state to history
        self.add_to_history(self.state)
    
    def _default_function(self, *args):
        """Default function that simulates work by sleeping"""
        for i in range(10):
            time.sleep(0.1)
            self.progress = (i + 1) * 10
            if self.state == ThreadState.TERMINATED:
                break
    
    def start(self):
        """Start the thread execution"""
        self.state = ThreadState.READY
        self.add_to_history(self.state)
        
    def run(self):
        """Execute the thread"""
        self.state = ThreadState.RUNNING
        self.start_time = time.time()
        self.add_to_history(self.state)
        self.function(*self.args)
        self.terminate()
        
    def block(self, resource=None):
        """Block the thread"""
        if self.state != ThreadState.TERMINATED:
            self.state = ThreadState.BLOCKED
            self.blocked_by = resource
            self.add_to_history(self.state)
        
    def unblock(self):
        """Unblock the thread"""
        if self.state == ThreadState.BLOCKED:
            self.state = ThreadState.READY
            self.blocked_by = None
            self.add_to_history(self.state)
        
    def terminate(self):
        """Terminate the thread"""
        self.state = ThreadState.TERMINATED
        self.end_time = time.time()
        if self.start_time:
            self.execution_time = self.end_time - self.start_time
        self.add_to_history(self.state)
        
    def add_to_history(self, state):
        """Add state transition to history"""
        self.history.append({
            'state': state,
            'time': time.time()
        })

class Process:
    """Represents a process with multiple threads"""
    
    next_id = 1
    
    def __init__(self, name=None):
        self.id = Process.next_id
        Process.next_id += 1
        self.name = name or f"Process-{self.id}"
        self.threads = []
        self.kernel_threads = []  # For One-to-Many and Many-to-Many models
        
    def add_thread(self, thread):
        """Add a thread to this process"""
        self.threads.append(thread)
        
    def remove_thread(self, thread):
        """Remove a thread from this process"""
        if thread in self.threads:
            self.threads.remove(thread)

class ThreadingModel:
    """Base class for different threading models"""
    
    def __init__(self, model_type: ThreadModelType):
        self.model_type = model_type
        self.processes = []
        
    def add_process(self, process):
        """Add a process to the model"""
        self.processes.append(process)
        
    def run_simulation(self):
        """Run the simulation according to the model type"""
        raise NotImplementedError("Subclasses must implement this method")

class ManyToOneModel(ThreadingModel):
    """Many user-level threads mapped to one kernel thread"""
    
    def __init__(self):
        super().__init__(ThreadModelType.MANY_TO_ONE)
        
    def run_simulation(self, callback=None):
        """Simulate the Many-to-One model"""
        for process in self.processes:
            # One kernel thread manages all user threads
            def kernel_thread_func():
                # Process all threads sequentially
                for thread in process.threads:
                    thread.start()
                    thread.run()
                    if callback:
                        callback()
            
            # Create and start the kernel thread
            kernel_thread = threading.Thread(target=kernel_thread_func)
            process.kernel_threads = [kernel_thread]
            kernel_thread.start()

class OneToManyModel(ThreadingModel):
    """One user-level thread mapped to many kernel threads"""
    
    def __init__(self):
        super().__init__(ThreadModelType.ONE_TO_MANY)
        
    def run_simulation(self, callback=None):
        """Simulate the One-to-Many model"""
        for process in self.processes:
            process.kernel_threads = []
            
            # Each user thread gets its own kernel thread
            for thread in process.threads:
                thread.start()
                
                def kernel_thread_func(user_thread):
                    user_thread.run()
                    if callback:
                        callback()
                
                # Create and start kernel thread for this user thread
                kernel_thread = threading.Thread(
                    target=kernel_thread_func, 
                    args=(thread,)
                )
                process.kernel_threads.append(kernel_thread)
                thread.kernel_thread = kernel_thread
                kernel_thread.start()

class ManyToManyModel(ThreadingModel):
    """Many user-level threads mapped to many kernel threads (thread pool)"""
    
    def __init__(self, kernel_thread_count=2):
        super().__init__(ThreadModelType.MANY_TO_MANY)
        self.kernel_thread_count = kernel_thread_count
        
    def run_simulation(self, callback=None):
        """Simulate the Many-to-Many model"""
        for process in self.processes:
            # Create a thread pool
            from concurrent.futures import ThreadPoolExecutor
            
            def execute_thread(thread):
                thread.start()
                thread.run()
                if callback:
                    callback()
                return thread
            
            # Create thread pool with kernel_thread_count threads
            with ThreadPoolExecutor(max_workers=self.kernel_thread_count) as executor:
                # Submit all user threads to the pool
                futures = [executor.submit(execute_thread, thread) for thread in process.threads]
                process.kernel_threads = [f for f in futures]  # Not actual threads but maintain the relationship

class OneToOneModel(ThreadingModel):
    """One user-level thread mapped to one kernel thread"""
    
    def __init__(self):
        super().__init__(ThreadModelType.ONE_TO_ONE)
        
    def run_simulation(self, callback=None):
        """Simulate the One-to-One model"""
        for process in self.processes:
            process.kernel_threads = []
            
            # Each user thread gets its own dedicated kernel thread
            for thread in process.threads:
                thread.start()
                
                def kernel_thread_func(user_thread):
                    user_thread.run()
                    if callback:
                        callback()
                
                # Create and start kernel thread for this user thread
                kernel_thread = threading.Thread(
                    target=kernel_thread_func, 
                    args=(thread,)
                )
                process.kernel_threads.append(kernel_thread)
                thread.kernel_thread = kernel_thread
                kernel_thread.start()
