"""
Thread Simulator - Simulator Engine
This module provides the core simulation logic that coordinates threads, processes, and synchronization.
"""

import time
import threading
import random
from typing import List, Dict, Any, Callable
import traceback
from collections import deque

# Import logger for detailed error tracking
from logger import log_info, log_error, log_exception, log_debug

# Import model classes with error handling
try:
    from models import Thread, Process, ThreadState, ThreadModelType
    from models import ManyToOneModel, OneToManyModel, ManyToManyModel, OneToOneModel
    from synchronization import Semaphore, Monitor
except Exception as e:
    log_exception(e, "Failed to import model classes")
    raise

class ThreadSimulator:
    """Main simulator engine that manages the entire simulation"""
    
    def __init__(self):
        log_info("Initializing ThreadSimulator")
        try:
            self.processes = []
            self.threads = []
            self.semaphores = []
            self.monitors = []
            self.threading_model = None
            self.is_running = False
            self.is_paused = False
            self.update_callbacks = []  # Callbacks for UI updates
            self.simulation_speed = 1.0  # Speed multiplier
            self.current_time = 0
            self.simulation_thread = None
            self.lock = threading.Lock()
            self.simulation_accuracy = 0.01  # Smaller values increase accuracy
            self.thread_performance_data = {}  # Track performance metrics
            self.context_switches = 0
            self.resource_contentions = 0
            self.last_active_thread = None
            self.timeline_events = deque(maxlen=1000)  # Limit to prevent memory issues
            log_info("ThreadSimulator initialized successfully")
        except Exception as e:
            log_exception(e, "Failed to initialize ThreadSimulator")
            raise
        
    def create_process(self, name=None) -> Process:
        """Create a new process"""
        process = Process(name)
        self.processes.append(process)
        return process
        
    def create_thread(self, process, function=None, args=None, name=None) -> Thread:
        """Create a new thread and add it to a process"""
        thread = Thread(name, function, args)
        self.threads.append(thread)
        process.add_thread(thread)
        
        # Initialize performance tracking for this thread
        self.thread_performance_data[thread.id] = {
            'wait_time': 0,
            'run_time': 0,
            'blocked_time': 0,
            'context_switches': 0,
            'started_at': None,
            'last_state_change': time.time(),
            'state_durations': {state.name: 0 for state in ThreadState}
        }
        return thread
    
    def create_semaphore(self, value=1, name=None) -> Semaphore:
        """Create a new semaphore"""
        semaphore = Semaphore(value, name or f"Semaphore-{len(self.semaphores)+1}")
        self.semaphores.append(semaphore)
        return semaphore
    
    def create_monitor(self, name=None) -> Monitor:
        """Create a new monitor"""
        monitor = Monitor(name or f"Monitor-{len(self.monitors)+1}")
        self.monitors.append(monitor)
        return monitor
    
    def set_threading_model(self, model_type: ThreadModelType, **kwargs):
        """Set the threading model for the simulation"""
        if model_type == ThreadModelType.MANY_TO_ONE:
            self.threading_model = ManyToOneModel()
        elif model_type == ThreadModelType.ONE_TO_MANY:
            self.threading_model = OneToManyModel()
        elif model_type == ThreadModelType.MANY_TO_MANY:
            # Get kernel thread count from kwargs or use default
            kernel_thread_count = kwargs.get('kernel_thread_count', 2)
            self.threading_model = ManyToManyModel(kernel_thread_count)
        elif model_type == ThreadModelType.ONE_TO_ONE:
            self.threading_model = OneToOneModel()
        else:
            raise ValueError(f"Unknown threading model type: {model_type}")
        
        # Add all processes to the model
        for process in self.processes:
            self.threading_model.add_process(process)
            
        log_info(f"Set threading model to {model_type.value}")
    
    def _track_state_change(self, thread, new_state):
        """Track thread state changes for analytics"""
        now = time.time()
        perf_data = self.thread_performance_data.get(thread.id)
        
        if not perf_data:
            # Thread not found in performance data
            return
            
        if thread.state == new_state:
            # No state change
            return
            
        # Record time spent in previous state
        time_in_state = now - perf_data['last_state_change']
        perf_data['state_durations'][thread.state.name] += time_in_state
        
        # Record specific metrics based on states
        if thread.state == ThreadState.READY and new_state == ThreadState.RUNNING:
            # Thread was waiting and is now running
            perf_data['wait_time'] += time_in_state
            perf_data['context_switches'] += 1
            self.context_switches += 1
            
            # Check if we're switching from another thread (context switch)
            if self.last_active_thread and self.last_active_thread != thread:
                self.timeline_events.append({
                    'type': 'context_switch',
                    'time': now,
                    'from_thread': self.last_active_thread.id,
                    'to_thread': thread.id
                })
            
            self.last_active_thread = thread
            
        elif thread.state == ThreadState.RUNNING and new_state == ThreadState.BLOCKED:
            # Thread was running and is now blocked
            perf_data['run_time'] += time_in_state
            
            # Record contention event
            self.resource_contentions += 1
            self.timeline_events.append({
                'type': 'resource_contention',
                'time': now,
                'thread': thread.id,
                'resource': thread.blocked_by.name if thread.blocked_by else "Unknown"
            })
            
        elif thread.state == ThreadState.BLOCKED and new_state == ThreadState.READY:
            # Thread was blocked and is now ready
            perf_data['blocked_time'] += time_in_state
            
        # If this is the first time we're seeing this thread active
        if new_state == ThreadState.RUNNING and perf_data['started_at'] is None:
            perf_data['started_at'] = now
            
        # Update last state change time
        perf_data['last_state_change'] = now
    
    def register_update_callback(self, callback: Callable):
        """Register a callback function to be called when simulation state changes"""
        self.update_callbacks.append(callback)
    
    def _notify_update(self):
        """Notify all registered callbacks about a state update"""
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                log_exception(e, f"Error in update callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")
                # Continue with other callbacks even if one fails
    
    def start_simulation(self):
        """Start the simulation"""
        if not self.threading_model:
            raise ValueError("Threading model not set")
        
        # Don't start a new simulation if one is already running
        if self.simulation_thread and self.simulation_thread.is_alive():
            if self.is_paused:
                self.resume_simulation()
            return
            
        log_info("Starting simulation")
        
        def simulation_runner():
            try:
                self.is_running = True
                self.is_paused = False
                self.current_time = 0
                self.context_switches = 0
                self.resource_contentions = 0
                self.last_active_thread = None
                self.timeline_events.clear()
                
                # Reset performance tracking
                for thread_id in self.thread_performance_data:
                    self.thread_performance_data[thread_id] = {
                        'wait_time': 0,
                        'run_time': 0,
                        'blocked_time': 0,
                        'context_switches': 0,
                        'started_at': None,
                        'last_state_change': time.time(),
                        'state_durations': {state.name: 0 for state in ThreadState}
                    }
                
                # Reset all threads to NEW state
                for thread in self.threads:
                    thread.state = ThreadState.NEW
                    thread.progress = 0
                
                # Reset all synchronization primitives
                for semaphore in self.semaphores:
                    semaphore.reset()
                for monitor in self.monitors:
                    monitor.reset()
                    
                # Register a state change monitor to thread models
                def state_change_monitor(thread, new_state):
                    self._track_state_change(thread, new_state)
                
                # Set up state change monitoring in model classes
                # This is a bit of a hack, but it's the easiest way to monitor state changes
                original_thread_run = Thread.run
                original_thread_block = Thread.block
                original_thread_unblock = Thread.unblock
                original_thread_terminate = Thread.terminate
                
                def new_run(self):
                    state_change_monitor(self, ThreadState.RUNNING)
                    original_thread_run(self)
                    
                def new_block(self, resource=None):
                    state_change_monitor(self, ThreadState.BLOCKED)
                    original_thread_block(self, resource)
                    
                def new_unblock(self):
                    state_change_monitor(self, ThreadState.READY)
                    original_thread_unblock(self)
                    
                def new_terminate(self):
                    state_change_monitor(self, ThreadState.TERMINATED)
                    original_thread_terminate(self)
                
                # Apply the modified methods
                Thread.run = new_run
                Thread.block = new_block
                Thread.unblock = new_unblock
                Thread.terminate = new_terminate
                
                try:
                    # Start the simulation according to the threading model
                    self.threading_model.run_simulation(callback=self._notify_update)
                finally:
                    # Restore original methods
                    Thread.run = original_thread_run
                    Thread.block = original_thread_block
                    Thread.unblock = original_thread_unblock
                    Thread.terminate = original_thread_terminate
                
                # When simulation completes
                log_info("Simulation complete")
            except Exception as e:
                log_exception(e, "Error in simulation runner")
                self.is_running = False
                self.is_paused = False
        
        self.simulation_thread = threading.Thread(target=simulation_runner)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        self._notify_update()
    
    def stop_simulation(self):
        """Stop the simulation"""
        if not self.is_running and not self.is_paused:
            return
            
        log_info("Stopping simulation")
        self.is_running = False
        self.is_paused = False
        
        # Terminate all threads
        for thread in self.threads:
            if thread.state != ThreadState.TERMINATED:
                thread.terminate()
                
        # Make sure callback is called to update UI
        self._notify_update()
    
    def pause_simulation(self):
        """Pause the simulation"""
        if not self.is_running or self.is_paused:
            return
            
        log_info("Pausing simulation")
        self.is_paused = True
        self.is_running = False
        self._notify_update()
    
    def resume_simulation(self):
        """Resume the simulation"""
        if not self.is_paused:
            return
            
        log_info("Resuming simulation")
        self.is_paused = False
        self.is_running = True
        self._notify_update()
    
    def reset_simulation(self):
        """Reset the simulation to its initial state"""
        log_info("Resetting simulation")
        self.stop_simulation()
        
        # Reset all collections
        self.threads = []
        self.processes = []
        self.semaphores = []
        self.monitors = []
        self.threading_model = None
        self.current_time = 0
        self.thread_performance_data = {}
        self.context_switches = 0
        self.resource_contentions = 0
        self.timeline_events.clear()
        
        # Make sure callback is called to update UI
        self._notify_update()
    
    def set_simulation_speed(self, speed: float):
        """Set the simulation speed multiplier"""
        self.simulation_speed = max(0.1, min(10.0, speed))
        log_debug(f"Set simulation speed to {self.simulation_speed}")
    
    def get_thread_efficiency(self, thread_id):
        """Calculate thread efficiency metrics"""
        perf_data = self.thread_performance_data.get(thread_id)
        if not perf_data:
            return None
            
        total_time = perf_data['run_time'] + perf_data['wait_time'] + perf_data['blocked_time']
        if total_time == 0:
            return {
                'cpu_utilization': 0,
                'wait_ratio': 0,
                'blocked_ratio': 0
            }
            
        return {
            'cpu_utilization': perf_data['run_time'] / total_time * 100 if total_time > 0 else 0,
            'wait_ratio': perf_data['wait_time'] / total_time * 100 if total_time > 0 else 0,
            'blocked_ratio': perf_data['blocked_time'] / total_time * 100 if total_time > 0 else 0
        }
    
    def get_performance_stats(self):
        """Get detailed performance statistics for the simulation"""
        stats = {
            'context_switches': self.context_switches,
            'resource_contentions': self.resource_contentions,
            'thread_stats': {},
            'overall_cpu_utilization': 0,
            'recent_events': list(self.timeline_events)[-10:] if self.timeline_events else []
        }
        
        total_run_time = 0
        total_time = 0
        
        # Calculate per-thread stats
        for thread in self.threads:
            thread_id = thread.id
            perf_data = self.thread_performance_data.get(thread_id)
            if not perf_data:
                continue
                
            efficiency = self.get_thread_efficiency(thread_id)
            if not efficiency:
                continue
                
            stats['thread_stats'][thread_id] = {
                'name': thread.name,
                'state': thread.state.name,
                'wait_time': perf_data['wait_time'],
                'run_time': perf_data['run_time'],
                'blocked_time': perf_data['blocked_time'],
                'context_switches': perf_data['context_switches'],
                'cpu_utilization': efficiency['cpu_utilization'],
                'state_durations': perf_data['state_durations']
            }
            
            total_run_time += perf_data['run_time']
            total_time += (perf_data['run_time'] + perf_data['wait_time'] + perf_data['blocked_time'])
        
        # Calculate overall CPU utilization
        if total_time > 0:
            stats['overall_cpu_utilization'] = total_run_time / total_time * 100
        
        return stats
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get statistics about the current simulation"""
        stats = {
            'process_count': len(self.processes),
            'thread_count': len(self.threads),
            'thread_states': {},
            'semaphores': [],
            'monitors': [],
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_time': self.current_time,
            'simulation_speed': self.simulation_speed,
            'context_switches': self.context_switches,
            'resource_contentions': self.resource_contentions
        }
        
        # Count threads by state
        for state in ThreadState:
            stats['thread_states'][state.name] = len([t for t in self.threads if t.state == state])
        
        # Collect semaphore info
        for semaphore in self.semaphores:
            stats['semaphores'].append({
                'name': semaphore.name,
                'value': semaphore.value,
                'waiting_threads': len(semaphore.waiting_threads),
                'log': semaphore.log[-10:] if semaphore.log else []  # Last 10 log entries
            })
        
        # Collect monitor info
        for monitor in self.monitors:
            monitor_stats = {
                'name': monitor.name,
                'log': monitor.log[-10:] if monitor.log else [],  # Last 10 log entries
                'condition_vars': {}
            }
            
            for name, cv in monitor.condition_vars.items():
                monitor_stats['condition_vars'][name] = {
                    'waiting_threads': len(cv.waiting_threads),
                    'log': cv.log[-10:] if cv.log else []  # Last 10 log entries
                }
                
            stats['monitors'].append(monitor_stats)
        
        return stats
    
    def export_simulation_data(self, filename=None):
        """Export simulation data to a JSON file"""
        import json
        from datetime import datetime
        
        if not filename:
            # Generate a default filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thread_simulation_{timestamp}.json"
        
        export_data = {
            'model_type': self.threading_model.__class__.__name__ if self.threading_model else None,
            'thread_count': len(self.threads),
            'process_count': len(self.processes),
            'simulation_time': self.current_time,
            'performance_stats': self.get_performance_stats(),
            'simulation_stats': self.get_simulation_stats(),
            'thread_histories': {
                t.id: [{'state': h['state'].name, 'time': h['time']} for h in t.history] 
                for t in self.threads
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            return True, filename
        except Exception as e:
            log_exception(e, f"Failed to export simulation data to {filename}")
            return False, str(e)
    
    def create_example_simulation(self, model_type=ThreadModelType.MANY_TO_ONE):
        """Create an example simulation setup"""
        log_info(f"Creating example simulation with model: {model_type}")
        try:
            self.reset_simulation()
            
            # Create process
            process = self.create_process("Example Process")
            log_debug(f"Created process: {process.name}")
            
            # Create semaphore
            semaphore = self.create_semaphore(1, "Resource Semaphore")
            log_debug(f"Created semaphore: {semaphore.name}")
            
            # Define thread function with semaphore usage
            def thread_function(thread_id, sem):
                try:
                    # Defensive check to make sure thread_id is valid
                    if thread_id < 0 or thread_id >= len(self.threads):
                        log_error(f"Invalid thread_id: {thread_id}, max: {len(self.threads)-1}")
                        return
                    
                    log_debug(f"Thread function started for thread_id: {thread_id}")
                    # Try to acquire the semaphore
                    while not sem.wait(self.threads[thread_id]):
                        time.sleep(0.1 / self.simulation_speed)
                    
                    # Critical section (simulate work)
                    for i in range(10):
                        if not self.is_running:
                            break
                        time.sleep(0.2 / self.simulation_speed)
                        self.threads[thread_id].progress = (i + 1) * 10
                    
                    # Release the semaphore
                    sem.signal(self.threads[thread_id])
                    log_debug(f"Thread function completed for thread_id: {thread_id}")
                except Exception as e:
                    log_exception(e, f"Error in thread_function for thread_id: {thread_id}")
            
            # Create threads
            log_debug("Creating threads for example simulation")
            for i in range(5):
                thread = self.create_thread(
                    process,
                    function=thread_function,
                    args=(i, semaphore),
                    name=f"Worker-{i+1}"
                )
                log_debug(f"Created thread: {thread.name}")
            
            # Set the threading model
            log_debug(f"Setting threading model to: {model_type}")
            self.set_threading_model(model_type)
            
            log_info("Example simulation created successfully")
            return self
        except Exception as e:
            log_exception(e, "Failed to create example simulation")
            raise
