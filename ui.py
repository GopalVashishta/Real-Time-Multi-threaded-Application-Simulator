"""
Thread Simulator - User Interface
This module provides the graphical user interface for the thread simulator.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from tkinter import simpledialog, filedialog
import threading
import time
import random
import json
from typing import Dict, List, Any, Tuple
import sys

# Import logger for detailed error tracking
from logger import log_info, log_error, log_exception, log_debug

# Import matplotlib with error handling
try:
    log_debug("Importing matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.animation as animation
    log_info("Matplotlib imported successfully")
except Exception as e:
    log_exception(e, "Failed to import matplotlib modules")
    raise

# Import simulator modules with error handling
try:
    log_debug("Importing simulator modules")
    from models import Thread, Process, ThreadState, ThreadModelType
    from synchronization import Semaphore, Monitor
    from simulator import ThreadSimulator
    log_info("Simulator modules imported successfully")
except Exception as e:
    log_exception(e, "Failed to import simulator modules")
    raise

class ThreadSimulatorUI:
    """Main UI class for the Thread Simulator"""
    
    def __init__(self, root):
        self.root = root
        log_info("Initializing ThreadSimulatorUI")
        
        try:
            # Create simulator instance
            log_debug("Creating ThreadSimulator instance")
            self.simulator = ThreadSimulator()
            self.simulator.register_update_callback(self.safe_update_ui)
            
            # Set UI sizes
            log_debug("Setting window geometry")
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)
            
            # Create the main frame
            log_debug("Creating main frame")
            self.main_frame = ttk.Frame(self.root)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create UI components with detailed error handling
            log_debug("Creating control panel")
            self._create_control_panel()
            
            log_debug("Creating visualization panel")
            self._create_visualization_panel()
            
            log_debug("Creating status bar")
            self._create_status_bar()
            
            # Set up initial UI state
            log_debug("Setting up initial UI state")
            self._setup_initial_ui_state()
            
            # Start UI update loop
            log_debug("Starting UI update loop")
            self._start_ui_update_loop()
            
            log_info("ThreadSimulatorUI initialization complete")
        except Exception as e:
            log_exception(e, "Failed to initialize ThreadSimulatorUI")
            raise
    
    def _create_control_panel(self):
        """Create the control panel with configuration options"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Control Panel")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Model selection
        model_frame = ttk.Frame(control_frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Threading Model:").pack(anchor=tk.W)
        
        self.model_var = tk.StringVar(value="Many-to-One")
        models = [
            "Many-to-One", 
            "One-to-Many", 
            "Many-to-Many",
            "One-to-One"
        ]
        
        model_dropdown = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var,
            values=models,
            state="readonly"
        )
        model_dropdown.pack(fill=tk.X, pady=2)
        
        # Thread count
        thread_frame = ttk.Frame(control_frame)
        thread_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(thread_frame, text="Number of Threads:").pack(anchor=tk.W)
        
        self.thread_count_var = tk.IntVar(value=5)
        thread_count_spinbox = ttk.Spinbox(
            thread_frame,
            from_=1,
            to=20,
            textvariable=self.thread_count_var
        )
        thread_count_spinbox.pack(fill=tk.X, pady=2)
        
        # Semaphore value
        semaphore_frame = ttk.Frame(control_frame)
        semaphore_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(semaphore_frame, text="Semaphore Value:").pack(anchor=tk.W)
        
        self.semaphore_value_var = tk.IntVar(value=2)
        semaphore_value_spinbox = ttk.Spinbox(
            semaphore_frame,
            from_=1,
            to=10,
            textvariable=self.semaphore_value_var
        )
        semaphore_value_spinbox.pack(fill=tk.X, pady=2)
        
        # Kernel threads (for Many-to-Many model)
        kernel_thread_frame = ttk.Frame(control_frame)
        kernel_thread_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(kernel_thread_frame, text="Kernel Threads (Many-to-Many):").pack(anchor=tk.W)
        
        self.kernel_thread_count_var = tk.IntVar(value=3)
        kernel_thread_count_spinbox = ttk.Spinbox(
            kernel_thread_frame,
            from_=1,
            to=10,
            textvariable=self.kernel_thread_count_var
        )
        kernel_thread_count_spinbox.pack(fill=tk.X, pady=2)
        
        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Simulation",
            command=self._on_start_simulation
        )
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop Simulation",
            command=self._on_stop_simulation,
            state=tk.DISABLED
        )
        self.stop_button.pack(fill=tk.X, pady=2)
        
        self.reset_button = ttk.Button(
            button_frame, 
            text="Reset Simulation",
            command=self._on_reset_simulation
        )
        self.reset_button.pack(fill=tk.X, pady=2)
        
        # Simulation speed
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(speed_frame, text="Simulation Speed:").pack(anchor=tk.W)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(
            speed_frame,
            from_=0.1,
            to=3.0,
            variable=self.speed_var,
            command=self._on_speed_change
        )
        speed_scale.pack(fill=tk.X, pady=2)
        
        speed_label = ttk.Label(speed_frame, textvariable=self.speed_var)
        speed_label.pack(pady=2)
        
        # Help button
        help_button = ttk.Button(
            control_frame, 
            text="Help",
            command=self._show_help
        )
        help_button.pack(fill=tk.X, padx=5, pady=10)
    
    def _create_visualization_panel(self):
        """Create the visualization panel with thread state diagram"""
        try:
            # Create a notebook for multiple visualization tabs
            log_debug("Creating notebook for visualization tabs")
            self.notebook = ttk.Notebook(self.main_frame)
            self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Thread visualization tab
            log_debug("Creating thread visualization tab")
            self.thread_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.thread_frame, text="Threads")
            
            # Create a frame for the thread state diagram
            self.thread_view_frame = ttk.Frame(self.thread_frame)
            self.thread_view_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Matplotlib figure for thread visualization
            log_debug("Setting up matplotlib figure for thread visualization")
            try:
                plt.rcParams['figure.dpi'] = 100
                self.fig = plt.Figure(figsize=(8, 6), dpi=100, facecolor='white')
                self.ax = self.fig.add_subplot(111)
                self.ax.set_title('Thread States and Progress')
                self.ax.set_xlabel('Progress (%)')
                self.ax.set_xlim(0, 100)
                self.ax.set_ylim(-1, 1)  # Default range until threads are added
                
                # This line might cause issues if matplotlib backend isn't properly set
                log_debug("Creating FigureCanvasTkAgg instance")
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.thread_view_frame)
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Force a draw to detect any issues early
                log_debug("Drawing initial canvas")
                self.canvas.draw()
                log_info("Thread visualization canvas created successfully")
            except Exception as e:
                log_exception(e, "Failed to create matplotlib visualization")
                raise
            
            # Thread state legend
            self.legend_frame = ttk.LabelFrame(self.thread_frame, text="Thread States")
            self.legend_frame.pack(fill=tk.X, padx=5, pady=5)
            
            state_colors = {
                ThreadState.NEW: "lightgray",
                ThreadState.READY: "yellow",
                ThreadState.RUNNING: "green",
                ThreadState.BLOCKED: "red",
                ThreadState.TERMINATED: "black"
            }
            
            for i, (state, color) in enumerate(state_colors.items()):
                frame = ttk.Frame(self.legend_frame)
                frame.grid(row=i//3, column=i%3, padx=10, pady=5, sticky="w")
                
                color_box = tk.Canvas(frame, width=15, height=15, bg=color)
                color_box.pack(side=tk.LEFT, padx=2)
                
                ttk.Label(frame, text=state.value).pack(side=tk.LEFT)
            
            # Timeline visualization tab
            self.timeline_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.timeline_frame, text="Timeline")
            
            # Matplotlib figure for timeline visualization
            self.timeline_fig = plt.Figure(figsize=(8, 6), dpi=100)
            self.timeline_ax = self.timeline_fig.add_subplot(111)
            self.timeline_canvas = FigureCanvasTkAgg(self.timeline_fig, master=self.timeline_frame)
            self.timeline_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Synchronization visualization tab
            self.sync_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.sync_frame, text="Synchronization")
            
            # Create semaphore and monitor visualization
            self.sync_tree = ttk.Treeview(self.sync_frame)
            self.sync_tree["columns"] = ("type", "value", "waiting")
            self.sync_tree.heading("#0", text="Name")
            self.sync_tree.heading("type", text="Type")
            self.sync_tree.heading("value", text="Value")
            self.sync_tree.heading("waiting", text="Waiting Threads")
            
            self.sync_tree.column("#0", width=150)
            self.sync_tree.column("type", width=100)
            self.sync_tree.column("value", width=100)
            self.sync_tree.column("waiting", width=150)
            
            # Add scrollbars to the treeview
            sync_scrollbar_y = ttk.Scrollbar(self.sync_frame, orient="vertical", command=self.sync_tree.yview)
            sync_scrollbar_x = ttk.Scrollbar(self.sync_frame, orient="horizontal", command=self.sync_tree.xview)
            self.sync_tree.configure(yscrollcommand=sync_scrollbar_y.set, xscrollcommand=sync_scrollbar_x.set)
            
            # Use grid instead of pack for better control of scrollbar placement
            self.sync_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            sync_scrollbar_y.grid(row=0, column=1, sticky="ns")
            sync_scrollbar_x.grid(row=1, column=0, sticky="ew")
            
            # Configure grid weights to make the treeview expand properly
            self.sync_frame.rowconfigure(0, weight=1)
            self.sync_frame.columnconfigure(0, weight=1)
        except Exception as e:
            log_exception(e, "Failed to create visualization panel")
            raise
    
    def _create_status_bar(self):
        """Create a status bar at the bottom of the window"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            self.status_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.time_var = tk.StringVar(value="Time: 0.00s")
        time_label = ttk.Label(
            self.status_frame,
            textvariable=self.time_var,
            relief=tk.SUNKEN,
            width=15
        )
        time_label.pack(side=tk.RIGHT)
    
    def _setup_initial_ui_state(self):
        """Set up the initial state of the UI"""
        # Set window title
        self.root.title("Thread Simulator")
        
        try:
            # Create initial example simulation
            self.simulator.create_example_simulation()
            
            # Update UI
            self.update_ui()
        except Exception as e:
            print(f"Error setting up initial UI state: {e}")
            self.status_var.set(f"Error in initialization: {str(e)}")
    
    def _start_ui_update_loop(self):
        """Start a loop to update the UI at regular intervals using Tkinter's after method"""
        def schedule_next_update():
            self.update_ui()
            # Schedule the next update after 100ms
            self.root.after(100, schedule_next_update)
        
        # Start the first update
        self.root.after(100, schedule_next_update)
    
    def safe_update_ui(self):
        """Thread-safe wrapper for update_ui"""
        try:
            # Use after_idle to ensure we're calling update_ui from the main thread
            self.root.after_idle(self.update_ui)
        except Exception as e:
            log_exception(e, "Error in safe_update_ui")
    
    def update_ui(self):
        """Update all UI components with current simulator state"""
        try:
            # Always update time display
            if self.simulator.is_running:
                self.simulator.current_time += 0.1
                self.time_var.set(f"Time: {self.simulator.current_time:.2f}s")
            
            # Check if we have threads to update thread-specific UI elements
            if not self.simulator.threads:
                self.status_var.set("Ready - No threads created")
                return
            
            # Update status
            stats = self.simulator.get_simulation_stats()
            states = stats['thread_states']
            state_str = ", ".join([f"{state}: {count}" for state, count in states.items() if count > 0])
            self.status_var.set(f"Threads: {sum(states.values())} ({state_str})")
            
            # Use after methods to ensure UI operations happen in the main thread
            self.root.after_idle(self._update_thread_visualization)
            self.root.after_idle(self._update_timeline_visualization)
            self.root.after_idle(self._update_sync_visualization)
            self.root.after_idle(self._update_button_states)
        except Exception as e:
            log_exception(e, "Error updating UI")
            # Use root.after to update UI from main thread
            self.root.after_idle(lambda: self.status_var.set(f"Error: {str(e)}"))
    
    def _update_thread_visualization(self):
        """Update the thread state visualization"""
        # Clear the figure
        self.ax.clear()
        
        # Get the threads and their states
        threads = self.simulator.threads
        if not threads:
            return
        
        # Colors for different thread states
        state_colors = {
            ThreadState.NEW: "lightgray",
            ThreadState.READY: "yellow",
            ThreadState.RUNNING: "green",
            ThreadState.BLOCKED: "red",
            ThreadState.TERMINATED: "gray"
        }
        
        # Create the thread state visualization
        thread_names = [t.name for t in threads]
        thread_states = [t.state for t in threads]
        thread_progress = [t.progress for t in threads]
        
        # Plot thread progress bars
        y_pos = range(len(threads))
        bars = self.ax.barh(y_pos, thread_progress, height=0.5, 
                         color=[state_colors[state] for state in thread_states])
        
        # Set labels and titles
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(thread_names)
        self.ax.set_xlabel('Progress (%)')
        self.ax.set_xlim(0, 100)
        self.ax.set_title('Thread States and Progress')
        
        # Add state labels to the bars
        for i, (bar, state) in enumerate(zip(bars, thread_states)):
            self.ax.text(
                5, i, 
                state.value, 
                va='center', 
                color='black' if state != ThreadState.TERMINATED else 'white',
                fontweight='bold'
            )
        
        # Draw the canvas
        self.canvas.draw()
    
    def _update_timeline_visualization(self):
        """Update the thread timeline visualization"""
        # Clear the figure
        self.timeline_ax.clear()
        
        # Get the threads and their histories
        threads = self.simulator.threads
        if not threads:
            return
        
        # Colors for different thread states
        state_colors = {
            ThreadState.NEW: "lightgray",
            ThreadState.READY: "yellow",
            ThreadState.RUNNING: "green",
            ThreadState.BLOCKED: "red",
            ThreadState.TERMINATED: "black"
        }
        
        # Plot timeline for each thread
        thread_names = [t.name for t in threads]
        
        # Y-position for each thread
        y_positions = {thread.name: i for i, thread in enumerate(threads)}
        
        # Plot state transitions for each thread
        for thread in threads:
            history = thread.history
            if not history:
                continue
            
            for i in range(len(history) - 1):
                start_time = history[i]['time'] - history[0]['time']
                end_time = history[i + 1]['time'] - history[0]['time']
                state = history[i]['state']
                
                self.timeline_ax.plot(
                    [start_time, end_time],
                    [y_positions[thread.name], y_positions[thread.name]],
                    color=state_colors[state],
                    linewidth=8
                )
            
            # Plot current state until now
            if len(history) > 0:
                last_time = history[-1]['time'] - history[0]['time']
                now = max(last_time, self.simulator.current_time)
                
                self.timeline_ax.plot(
                    [last_time, now],
                    [y_positions[thread.name], y_positions[thread.name]],
                    color=state_colors[history[-1]['state']],
                    linewidth=8
                )
        
        # Set labels and titles
        self.timeline_ax.set_yticks(range(len(threads)))
        self.timeline_ax.set_yticklabels(thread_names)
        self.timeline_ax.set_xlabel('Time (s)')
        self.timeline_ax.set_title('Thread Timeline')
        
        # Adjust axes limits
        self.timeline_ax.set_xlim(0, max(0.1, self.simulator.current_time))
        
        # Draw the canvas
        self.timeline_canvas.draw()
    
    def _update_sync_visualization(self):
        """Update the synchronization primitives visualization"""
        try:
            # Clear the tree
            for item in self.sync_tree.get_children():
                self.sync_tree.delete(item)
            
            # Add semaphores
            for semaphore in self.simulator.semaphores:
                try:
                    waiting_count = len(semaphore.waiting_threads) if hasattr(semaphore, 'waiting_threads') else 0
                    self.sync_tree.insert(
                        "", 
                        "end",
                        text=str(semaphore.name),
                        values=("Semaphore", str(semaphore.value), str(waiting_count))
                    )
                except Exception as e:
                    log_error(f"Error adding semaphore to tree: {e}")
            
            # Add monitors
            for monitor in self.simulator.monitors:
                try:
                    monitor_id = self.sync_tree.insert(
                        "", 
                        "end",
                        text=str(monitor.name),
                        values=("Monitor", "", "")
                    )
                    
                    # Add condition variables if they exist
                    if hasattr(monitor, 'condition_vars'):
                        for name, cv in monitor.condition_vars.items():
                            waiting_count = len(cv.waiting_threads) if hasattr(cv, 'waiting_threads') else 0
                            self.sync_tree.insert(
                                monitor_id,
                                "end",
                                text=name,
                                values=("Condition Variable", "", str(waiting_count))
                            )
                except Exception as e:
                    log_error(f"Error adding monitor to tree: {e}")
        except Exception as e:
            log_exception(e, f"Error updating sync visualization: {e}")
    
    def _update_button_states(self):
        """Update the state of control buttons based on the simulator state"""
        if self.simulator.is_running:
            self.start_button.config(text="Pause", command=self._on_pause_simulation)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(text="Start", command=self._on_start_simulation)
    
    def _on_start_simulation(self):
        """Handle click on the Start/Resume button"""
        if not self.simulator.is_running:
            # If simulation is not running, set up a new one
            model_type_str = self.model_var.get()
            model_map = {
                "Many-to-One": ThreadModelType.MANY_TO_ONE,
                "One-to-Many": ThreadModelType.ONE_TO_MANY,
                "Many-to-Many": ThreadModelType.MANY_TO_MANY,
                "One-to-One": ThreadModelType.ONE_TO_ONE
            }
            
            model_type = model_map.get(model_type_str, ThreadModelType.MANY_TO_ONE)
            thread_count = self.thread_count_var.get()
            semaphore_value = self.semaphore_value_var.get()
            kernel_thread_count = self.kernel_thread_count_var.get()
            
            # Reset simulator
            self.simulator.reset_simulation()
            
            # Create process
            process = self.simulator.create_process("Main Process")
            
            # Create semaphore
            semaphore = self.simulator.create_semaphore(semaphore_value, "Resource Semaphore")
            
            # Define thread function with semaphore usage
            def thread_function(thread_id, sem):
                # Try to acquire the semaphore
                while not sem.wait(self.simulator.threads[thread_id]):
                    time.sleep(0.1 / self.simulator.simulation_speed)
                
                # Critical section (simulate work)
                for i in range(10):
                    if not self.simulator.is_running:
                        break
                    time.sleep(0.2 / self.simulator.simulation_speed)
                    self.simulator.threads[thread_id].progress = (i + 1) * 10
                
                # Release the semaphore
                sem.signal(self.simulator.threads[thread_id])
            
            # Create threads
            for i in range(thread_count):
                thread = self.simulator.create_thread(
                    process,
                    function=thread_function,
                    args=(i, semaphore),
                    name=f"Worker-{i+1}"
                )
            
            # Set the threading model
            kwargs = {}
            if model_type == ThreadModelType.MANY_TO_MANY:
                kwargs['kernel_thread_count'] = kernel_thread_count
            
            self.simulator.set_threading_model(model_type, **kwargs)
            
            # Start simulation
            self.simulator.start_simulation()
            
            # Update UI state
            self.start_button.config(text="Pause", command=self._on_pause_simulation)
            self.stop_button.config(state=tk.NORMAL)
        else:
            # Resume paused simulation
            self.simulator.resume_simulation()
            self.start_button.config(text="Pause", command=self._on_pause_simulation)
    
    def _on_pause_simulation(self):
        """Handle click on the Pause button"""
        self.simulator.pause_simulation()
        self.start_button.config(text="Resume", command=self._on_start_simulation)
    
    def _on_stop_simulation(self):
        """Handle click on the Stop button"""
        self.simulator.stop_simulation()
        self.start_button.config(text="Start", command=self._on_start_simulation)
        self.stop_button.config(state=tk.DISABLED)
    
    def _on_reset_simulation(self):
        """Handle click on the Reset button"""
        self.simulator.reset_simulation()
        self.start_button.config(text="Start", command=self._on_start_simulation)
        self.stop_button.config(state=tk.DISABLED)
        
        # Reset UI state
        self.thread_count_var.set(5)
        self.semaphore_value_var.set(2)
        self.kernel_thread_count_var.set(3)
        self.model_var.set("Many-to-One")
        self.speed_var.set(1.0)
        
        # Create an example simulation
        self.simulator.create_example_simulation()
        self.update_ui()
    
    def _on_speed_change(self, event):
        """Handle change in the simulation speed slider"""
        speed = self.speed_var.get()
        self.simulator.set_simulation_speed(speed)
    
    def _show_help(self):
        """Show help information"""
        help_text = """
Thread Simulator Help

This application simulates different thread models and synchronization mechanisms.

Threading Models:
- Many-to-One: Many user threads mapped to a single kernel thread
- One-to-Many: Each user thread mapped to many kernel threads
- Many-to-Many: User threads dynamically mapped to a pool of kernel threads
- One-to-One: Each user thread mapped to exactly one kernel thread

Controls:
- Number of Threads: How many user threads to create
- Semaphore Value: Initial value of the semaphore (max concurrent access)
- Kernel Threads: Number of kernel threads for Many-to-Many model
- Simulation Speed: Adjust how fast the simulation runs

Visualizations:
- Threads: Shows current state and progress of each thread
- Timeline: Shows thread state changes over time
- Synchronization: Shows semaphores and monitors with waiting threads
        """
        
        messagebox.showinfo("Thread Simulator Help", help_text)
