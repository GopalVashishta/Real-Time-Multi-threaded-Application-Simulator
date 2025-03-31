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
import os

# Import logger for detailed error tracking
from logger import log_info, log_error, log_exception, log_debug

# Import matplotlib with error handling
try:
    log_debug("Importing matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.animation as animation
    from matplotlib.figure import Figure
    plt.style.use('ggplot')  # Modern style for plots
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

# Try to import ttkthemes for better styling if available
try:
    from ttkthemes import ThemedTk, ThemedStyle
    THEMED_TK_AVAILABLE = True
    log_info("ttkthemes package is available and imported")
except ImportError:
    THEMED_TK_AVAILABLE = False
    log_info("ttkthemes package not available, using standard ttk styling")

class ThreadSimulatorUI:
    """Main UI class for the Thread Simulator"""
    
    # Modern color schemes
    LIGHT_THEME = {
        "bg": "#f5f5f5",
        "fg": "#212121",
        "accent": "#2196f3",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "chart_colors": {
            ThreadState.NEW: "#9e9e9e",  # Light gray
            ThreadState.READY: "#ffeb3b", # Yellow
            ThreadState.RUNNING: "#4caf50", # Green
            ThreadState.BLOCKED: "#f44336", # Red
            ThreadState.TERMINATED: "#212121" # Black
        }
    }
    
    DARK_THEME = {
        "bg": "#212121",
        "fg": "#f5f5f5",
        "accent": "#2196f3",
        "success": "#4caf50",
        "warning": "#ff9800",
        "error": "#f44336",
        "chart_colors": {
            ThreadState.NEW: "#757575",  # Gray
            ThreadState.READY: "#fff176", # Light yellow
            ThreadState.RUNNING: "#81c784", # Light green
            ThreadState.BLOCKED: "#e57373", # Light red
            ThreadState.TERMINATED: "#9e9e9e" # Light gray
        }
    }
    
    def __init__(self, root):
        self.root = root
        log_info("Initializing ThreadSimulatorUI")
        
        try:
            # Apply modern theme
            self._setup_theme()
            
            # Create simulator instance
            log_debug("Creating ThreadSimulator instance")
            self.simulator = ThreadSimulator()
            self.simulator.register_update_callback(self.safe_update_ui)
            
            # Current theme
            self.current_theme = self.LIGHT_THEME
            
            # Set UI sizes
            log_debug("Setting window geometry")
            self.root.geometry("1200x800")
            self.root.minsize(800, 600)
            
            # Create menu
            self._create_menu()
            
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
            
            # Setup tooltips
            self._setup_tooltips()
            
            log_info("ThreadSimulatorUI initialization complete")
        except Exception as e:
            log_exception(e, "Failed to initialize ThreadSimulatorUI")
            raise
    
    def _setup_theme(self):
        """Set up the UI theme"""
        if THEMED_TK_AVAILABLE and isinstance(self.root, ThemedTk):
            # Root is already a ThemedTk
            self.style = ThemedStyle(self.root)
            self.style.set_theme("arc")  # Modern, flat theme
        else:
            # Use standard ttk styling
            self.style = ttk.Style()
            if sys.platform == "darwin":  # macOS
                self.style.theme_use("aqua")
            elif sys.platform == "win32":  # Windows
                self.style.theme_use("vista")
            else:  # Linux and others
                self.style.theme_use("clam")
        
        # Configure custom styles
        self.style.configure("TButton", padding=6, relief="flat", background="#2196f3")
        self.style.configure("Accent.TButton", background="#2196f3", foreground="white")
        self.style.map("Accent.TButton",
            background=[("active", "#1976d2"), ("pressed", "#0d47a1")],
            foreground=[("active", "white"), ("pressed", "white")])
        
        self.style.configure("Success.TButton", background="#4caf50", foreground="white")
        self.style.map("Success.TButton",
            background=[("active", "#388e3c"), ("pressed", "#1b5e20")],
            foreground=[("active", "white"), ("pressed", "white")])
        
        self.style.configure("Warning.TButton", background="#ff9800", foreground="white")
        self.style.map("Warning.TButton",
            background=[("active", "#f57c00"), ("pressed", "#e65100")],
            foreground=[("active", "white"), ("pressed", "white")])
        
        self.style.configure("Error.TButton", background="#f44336", foreground="white")
        self.style.map("Error.TButton",
            background=[("active", "#d32f2f"), ("pressed", "#b71c1c")],
            foreground=[("active", "white"), ("pressed", "white")])
    
    def _create_menu(self):
        """Create main menu bar"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New Simulation", command=self._on_reset_simulation)
        file_menu.add_separator()
        file_menu.add_command(label="Export Simulation Data", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        
        # Theme submenu
        theme_menu = tk.Menu(edit_menu, tearoff=0)
        self.theme_var = tk.StringVar(value="Light")
        theme_menu.add_radiobutton(label="Light", variable=self.theme_var, value="Light", command=self._set_light_theme)
        theme_menu.add_radiobutton(label="Dark", variable=self.theme_var, value="Dark", command=self._set_dark_theme)
        edit_menu.add_cascade(label="Theme", menu=theme_menu)
        
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Reset Layout", command=self._reset_layout)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Help", command=self._show_help)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
    
    def _create_control_panel(self):
        """Create the control panel with configuration options"""
        control_frame = ttk.LabelFrame(self.main_frame, text="Control Panel")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Main settings frame
        settings_frame = ttk.Frame(control_frame)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model selection with header
        model_header = ttk.Label(settings_frame, text="Simulation Settings", font=("Helvetica", 12, "bold"))
        model_header.pack(anchor=tk.W, pady=(5, 10))
        
        model_frame = ttk.Frame(settings_frame)
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
        thread_frame = ttk.Frame(settings_frame)
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
        semaphore_frame = ttk.Frame(settings_frame)
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
        kernel_thread_frame = ttk.Frame(settings_frame)
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
        
        # Simulation control header
        control_header = ttk.Label(control_frame, text="Simulation Control", font=("Helvetica", 12, "bold"))
        control_header.pack(anchor=tk.W, pady=(15, 10), padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Simulation",
            command=self._on_start_simulation,
            style="Accent.TButton"
        )
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="Stop Simulation",
            command=self._on_stop_simulation,
            state=tk.DISABLED,
            style="Error.TButton"
        )
        self.stop_button.pack(fill=tk.X, pady=2)
        
        self.reset_button = ttk.Button(
            button_frame, 
            text="Reset Simulation",
            command=self._on_reset_simulation,
            style="Warning.TButton"
        )
        self.reset_button.pack(fill=tk.X, pady=2)
        
        # Simulation speed
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Speed label with value
        speed_header_frame = ttk.Frame(speed_frame)
        speed_header_frame.pack(fill=tk.X)
        
        ttk.Label(speed_header_frame, text="Simulation Speed:").pack(side=tk.LEFT)
        self.speed_label = ttk.Label(speed_header_frame, text="1.0x")
        self.speed_label.pack(side=tk.RIGHT)
        
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(
            speed_frame,
            from_=0.1,
            to=3.0,
            variable=self.speed_var,
            command=self._on_speed_change
        )
        speed_scale.pack(fill=tk.X, pady=2)
        
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
                self.fig = Figure(figsize=(8, 6), dpi=100, facecolor=self.current_theme["bg"])
                self.ax = self.fig.add_subplot(111)
                self.ax.set_title('Thread States and Progress', color=self.current_theme["fg"])
                self.ax.set_xlabel('Progress (%)', color=self.current_theme["fg"])
                self.ax.set_xlim(0, 100)
                self.ax.set_ylim(-1, 1)  # Default range until threads are added
                
                # Customize plot styling
                self.fig.patch.set_facecolor(self.current_theme["bg"])
                self.ax.set_facecolor(self.current_theme["bg"])
                self.ax.spines['bottom'].set_color(self.current_theme["fg"])
                self.ax.spines['top'].set_color(self.current_theme["fg"])
                self.ax.spines['right'].set_color(self.current_theme["fg"])
                self.ax.spines['left'].set_color(self.current_theme["fg"])
                self.ax.tick_params(axis='x', colors=self.current_theme["fg"])
                self.ax.tick_params(axis='y', colors=self.current_theme["fg"])
                
                # This line might cause issues if matplotlib backend isn't properly set
                log_debug("Creating FigureCanvasTkAgg instance")
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.thread_view_frame)
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # Create toolbar for thread visualization
                from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                self.toolbar = NavigationToolbar2Tk(self.canvas, self.thread_view_frame)
                self.toolbar.update()
                
                # Force a draw to detect any issues early
                log_debug("Drawing initial canvas")
                self.canvas.draw()
                log_info("Thread visualization canvas created successfully")
            except Exception as e:
                log_exception(e, "Failed to create matplotlib visualization")
                raise
            
            # Thread state legend with modern styling
            self.legend_frame = ttk.LabelFrame(self.thread_frame, text="Thread States")
            self.legend_frame.pack(fill=tk.X, padx=5, pady=5)
            
            legend_inner_frame = ttk.Frame(self.legend_frame)
            legend_inner_frame.pack(fill=tk.X, padx=10, pady=10)
            
            state_colors = self.current_theme["chart_colors"]
            
            for i, (state, color) in enumerate(state_colors.items()):
                frame = ttk.Frame(legend_inner_frame)
                frame.grid(row=i//3, column=i%3, padx=15, pady=8, sticky="w")
                
                color_box = tk.Canvas(frame, width=18, height=18, bg=color, highlightthickness=0)
                color_box.pack(side=tk.LEFT, padx=5)
                
                ttk.Label(frame, text=state.value, font=("Helvetica", 10)).pack(side=tk.LEFT)
            
            # Timeline visualization tab
            self.timeline_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.timeline_frame, text="Timeline")
            
            # Matplotlib figure for timeline visualization
            self.timeline_fig = Figure(figsize=(8, 6), dpi=100, facecolor=self.current_theme["bg"])
            self.timeline_ax = self.timeline_fig.add_subplot(111)
            
            # Customize plot styling
            self.timeline_fig.patch.set_facecolor(self.current_theme["bg"])
            self.timeline_ax.set_facecolor(self.current_theme["bg"])
            self.timeline_ax.set_title('Thread Timeline', color=self.current_theme["fg"])
            self.timeline_ax.set_xlabel('Time (s)', color=self.current_theme["fg"])
            self.timeline_ax.spines['bottom'].set_color(self.current_theme["fg"])
            self.timeline_ax.spines['top'].set_color(self.current_theme["fg"])
            self.timeline_ax.spines['right'].set_color(self.current_theme["fg"])
            self.timeline_ax.spines['left'].set_color(self.current_theme["fg"])
            self.timeline_ax.tick_params(axis='x', colors=self.current_theme["fg"])
            self.timeline_ax.tick_params(axis='y', colors=self.current_theme["fg"])
            
            self.timeline_canvas = FigureCanvasTkAgg(self.timeline_fig, master=self.timeline_frame)
            self.timeline_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Create toolbar for timeline visualization
            self.timeline_toolbar = NavigationToolbar2Tk(self.timeline_canvas, self.timeline_frame)
            self.timeline_toolbar.update()
            
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
            
            # Analytics tab - NEW
            self.analytics_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.analytics_frame, text="Analytics")
            
            # Set up the analytics tab with paned window for flexibility
            self.analytics_pane = ttk.PanedWindow(self.analytics_frame, orient=tk.HORIZONTAL)
            self.analytics_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Left side: Thread performance metrics
            self.performance_frame = ttk.LabelFrame(self.analytics_pane, text="Thread Performance")
            self.analytics_pane.add(self.performance_frame, weight=1)
            
            # Treeview for thread performance stats
            self.perf_tree = ttk.Treeview(self.performance_frame)
            self.perf_tree["columns"] = ("cpu", "wait", "blocked", "switches")
            self.perf_tree.heading("#0", text="Thread")
            self.perf_tree.heading("cpu", text="CPU %")
            self.perf_tree.heading("wait", text="Wait %")
            self.perf_tree.heading("blocked", text="Blocked %")
            self.perf_tree.heading("switches", text="Context Switches")
            
            self.perf_tree.column("#0", width=120)
            self.perf_tree.column("cpu", width=70, anchor=tk.CENTER)
            self.perf_tree.column("wait", width=70, anchor=tk.CENTER)
            self.perf_tree.column("blocked", width=70, anchor=tk.CENTER)
            self.perf_tree.column("switches", width=120, anchor=tk.CENTER)
            
            # Add scrollbars to the treeview
            perf_scrollbar_y = ttk.Scrollbar(self.performance_frame, orient="vertical", command=self.perf_tree.yview)
            perf_scrollbar_x = ttk.Scrollbar(self.performance_frame, orient="horizontal", command=self.perf_tree.xview)
            self.perf_tree.configure(yscrollcommand=perf_scrollbar_y.set, xscrollcommand=perf_scrollbar_x.set)
            
            # Use grid for better control of scrollbar placement
            self.perf_tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            perf_scrollbar_y.grid(row=0, column=1, sticky="ns")
            perf_scrollbar_x.grid(row=1, column=0, sticky="ew")
            
            # Configure grid weights
            self.performance_frame.rowconfigure(0, weight=1)
            self.performance_frame.columnconfigure(0, weight=1)
            
            # Right side: Performance charts
            self.charts_frame = ttk.LabelFrame(self.analytics_pane, text="Performance Charts")
            self.analytics_pane.add(self.charts_frame, weight=1)
            
            # Matplotlib figure for performance visualization
            self.perf_fig = Figure(figsize=(6, 6), dpi=100, facecolor=self.current_theme["bg"])
            self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, master=self.charts_frame)
            self.perf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create two subplots for different metrics
            gs = self.perf_fig.add_gridspec(2, 1)
            self.cpu_ax = self.perf_fig.add_subplot(gs[0, 0])
            self.event_ax = self.perf_fig.add_subplot(gs[1, 0])
            
            # Style the chart
            self.perf_fig.patch.set_facecolor(self.current_theme["bg"])
            for ax in [self.cpu_ax, self.event_ax]:
                ax.set_facecolor(self.current_theme["bg"])
                ax.spines['bottom'].set_color(self.current_theme["fg"])
                ax.spines['top'].set_color(self.current_theme["fg"])
                ax.spines['right'].set_color(self.current_theme["fg"])
                ax.spines['left'].set_color(self.current_theme["fg"])
                ax.tick_params(axis='x', colors=self.current_theme["fg"])
                ax.tick_params(axis='y', colors=self.current_theme["fg"])
            
            # Set titles
            self.cpu_ax.set_title('CPU Utilization per Thread', color=self.current_theme["fg"])
            self.event_ax.set_title('Events Timeline', color=self.current_theme["fg"])
            
            # Bottom frame for overall stats
            self.overall_stats_frame = ttk.Frame(self.analytics_frame)
            self.overall_stats_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Overall statistics display
            stat_frame = ttk.LabelFrame(self.overall_stats_frame, text="Overall Statistics")
            stat_frame.pack(fill=tk.X, padx=5, pady=5)
            
            stat_grid = ttk.Frame(stat_frame)
            stat_grid.pack(fill=tk.X, padx=10, pady=10)
            
            # Context switches
            ttk.Label(stat_grid, text="Context Switches:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
            self.context_switch_var = tk.StringVar(value="0")
            ttk.Label(stat_grid, textvariable=self.context_switch_var, font=("Helvetica", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=3)
            
            # Resource contentions
            ttk.Label(stat_grid, text="Resource Contentions:").grid(row=0, column=2, sticky="w", padx=5, pady=3)
            self.contention_var = tk.StringVar(value="0")
            ttk.Label(stat_grid, textvariable=self.contention_var, font=("Helvetica", 10, "bold")).grid(row=0, column=3, sticky="w", padx=5, pady=3)
            
            # Overall CPU utilization
            ttk.Label(stat_grid, text="Overall CPU Utilization:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
            self.cpu_util_var = tk.StringVar(value="0.0%")
            ttk.Label(stat_grid, textvariable=self.cpu_util_var, font=("Helvetica", 10, "bold")).grid(row=1, column=1, sticky="w", padx=5, pady=3)
            
            # Export button
            export_button = ttk.Button(
                self.overall_stats_frame, 
                text="Export Simulation Data",
                command=self._export_data
            )
            export_button.pack(fill=tk.X, padx=5, pady=5)
            
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
            anchor=tk.W,
            padding=(5, 2)
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.time_var = tk.StringVar(value="Time: 0.00s")
        time_label = ttk.Label(
            self.status_frame,
            textvariable=self.time_var,
            relief=tk.SUNKEN,
            width=15,
            padding=(5, 2)
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
            log_exception(e, "Error setting up initial UI state")
            self.status_var.set(f"Error in initialization: {str(e)}")
    
    def _set_light_theme(self):
        """Switch to light theme"""
        self.current_theme = self.LIGHT_THEME
        self._apply_theme()
    
    def _set_dark_theme(self):
        """Switch to dark theme"""
        self.current_theme = self.DARK_THEME
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply the current theme to all UI components"""
        # Update plot backgrounds and text colors
        self.fig.patch.set_facecolor(self.current_theme["bg"])
        self.ax.set_facecolor(self.current_theme["bg"])
        self.ax.set_title('Thread States and Progress', color=self.current_theme["fg"])
        self.ax.set_xlabel('Progress (%)', color=self.current_theme["fg"])
        self.ax.spines['bottom'].set_color(self.current_theme["fg"])
        self.ax.spines['top'].set_color(self.current_theme["fg"])
        self.ax.spines['right'].set_color(self.current_theme["fg"])
        self.ax.spines['left'].set_color(self.current_theme["fg"])
        self.ax.tick_params(axis='x', colors=self.current_theme["fg"])
        self.ax.tick_params(axis='y', colors=self.current_theme["fg"])
        
        # Timeline plot
        self.timeline_fig.patch.set_facecolor(self.current_theme["bg"])
        self.timeline_ax.set_facecolor(self.current_theme["bg"])
        self.timeline_ax.set_title('Thread Timeline', color=self.current_theme["fg"])
        self.timeline_ax.set_xlabel('Time (s)', color=self.current_theme["fg"])
        self.timeline_ax.spines['bottom'].set_color(self.current_theme["fg"])
        self.timeline_ax.spines['top'].set_color(self.current_theme["fg"])
        self.timeline_ax.spines['right'].set_color(self.current_theme["fg"])
        self.timeline_ax.spines['left'].set_color(self.current_theme["fg"])
        self.timeline_ax.tick_params(axis='x', colors=self.current_theme["fg"])
        self.timeline_ax.tick_params(axis='y', colors=self.current_theme["fg"])
        
        # Apply theme to performance charts
        self.perf_fig.patch.set_facecolor(self.current_theme["bg"])
        for ax in [self.cpu_ax, self.event_ax]:
            ax.set_facecolor(self.current_theme["bg"])
            ax.set_title(ax.get_title(), color=self.current_theme["fg"])
            ax.spines['bottom'].set_color(self.current_theme["fg"])
            ax.spines['top'].set_color(self.current_theme["fg"])
            ax.spines['right'].set_color(self.current_theme["fg"])
            ax.spines['left'].set_color(self.current_theme["fg"])
            ax.tick_params(axis='x', colors=self.current_theme["fg"])
            ax.tick_params(axis='y', colors=self.current_theme["fg"])
        
        # Force redraw all canvases
        self.canvas.draw()
        self.timeline_canvas.draw()
        self.perf_canvas.draw()
        
        # Update UI
        self.update_ui()
    
    def _reset_layout(self):
        """Reset UI layout to default"""
        # Reset window size
        self.root.geometry("1200x800")
        
        # Redraw UI elements
        self.update_ui()
    
    def _start_ui_update_loop(self):
        """Start a loop to update the UI at regular intervals using Tkinter's after method"""
        def schedule_next_update():
            self.update_ui()
            # Schedule the next update after 100ms
            self.root.after(100, schedule_next_update)
        
        # Start the first update
        self.root.after(100, schedule_next_update)
    
    def _setup_tooltips(self):
        """Setup tooltips for UI elements"""
        # We'll implement a simple tooltip class
        class ToolTip:
            def __init__(self, widget, text):
                self.widget = widget
                self.text = text
                self.tip_window = None
                self.widget.bind("<Enter>", self.show_tip)
                self.widget.bind("<Leave>", self.hide_tip)
            
            def show_tip(self, event=None):
                "Display text in a tooltip window"
                x, y, _, _ = self.widget.bbox("insert")
                x += self.widget.winfo_rootx() + 25
                y += self.widget.winfo_rooty() + 25
                
                # Creates a toplevel window
                self.tip_window = tw = tk.Toplevel(self.widget)
                # Make it stay on top
                tw.wm_overrideredirect(True)
                tw.wm_geometry(f"+{x}+{y}")
                
                label = ttk.Label(tw, text=self.text, justify=tk.LEFT,
                              background="#ffffe0", relief=tk.SOLID, borderwidth=1)
                label.pack(ipadx=5, ipady=5)
            
            def hide_tip(self, event=None):
                if self.tip_window:
                    self.tip_window.destroy()
                    self.tip_window = None
        
        # Add tooltips to UI elements
        ToolTip(self.start_button, "Start or pause the simulation")
        ToolTip(self.stop_button, "Stop the current simulation")
        ToolTip(self.reset_button, "Reset to initial state")
    
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
            self.root.after_idle(self._update_performance_visualization)
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
        
        # Colors for different thread states from current theme
        state_colors = self.current_theme["chart_colors"]
        
        # Create the thread state visualization
        thread_names = [t.name for t in threads]
        thread_states = [t.state for t in threads]
        thread_progress = [t.progress for t in threads]
        
        # Plot thread progress bars
        y_pos = range(len(threads))
        bars = self.ax.barh(y_pos, thread_progress, height=0.5, 
                         color=[state_colors[state] for state in thread_states])
        
        # Set labels and titles with theme colors
        self.ax.set_yticks(y_pos)
        self.ax.set_yticklabels(thread_names, color=self.current_theme["fg"])
        self.ax.set_xlabel('Progress (%)', color=self.current_theme["fg"])
        self.ax.set_xlim(0, 100)
        self.ax.set_title('Thread States and Progress', color=self.current_theme["fg"])
        
        # Style grid
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # Style axes
        self.ax.set_facecolor(self.current_theme["bg"])
        self.ax.spines['bottom'].set_color(self.current_theme["fg"])
        self.ax.spines['top'].set_color(self.current_theme["fg"])
        self.ax.spines['right'].set_color(self.current_theme["fg"])
        self.ax.spines['left'].set_color(self.current_theme["fg"])
        self.ax.tick_params(axis='x', colors=self.current_theme["fg"])
        self.ax.tick_params(axis='y', colors=self.current_theme["fg"])
        
        # Add state labels to the bars
        for i, (bar, state) in enumerate(zip(bars, thread_states)):
            label_color = 'white' if state == ThreadState.TERMINATED else 'black'
            self.ax.text(
                5, i, 
                state.value, 
                va='center', 
                color=label_color,
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
        
        # Colors for different thread states from current theme
        state_colors = self.current_theme["chart_colors"]
        
        # Set background and text colors
        self.timeline_ax.set_facecolor(self.current_theme["bg"])
        self.timeline_ax.spines['bottom'].set_color(self.current_theme["fg"])
        self.timeline_ax.spines['top'].set_color(self.current_theme["fg"])
        self.timeline_ax.spines['right'].set_color(self.current_theme["fg"])
        self.timeline_ax.spines['left'].set_color(self.current_theme["fg"])
        
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
                    linewidth=10,
                    solid_capstyle='butt'
                )
            
            # Plot current state until now
            if len(history) > 0:
                last_time = history[-1]['time'] - history[0]['time']
                now = max(last_time, self.simulator.current_time)
                
                self.timeline_ax.plot(
                    [last_time, now],
                    [y_positions[thread.name], y_positions[thread.name]],
                    color=state_colors[history[-1]['state']],
                    linewidth=10,
                    solid_capstyle='butt'
                )
                
                # Add the current state as text label at the end of the line
                if history[-1]['state'] != ThreadState.TERMINATED:
                    self.timeline_ax.text(
                        now + 0.1, 
                        y_positions[thread.name], 
                        history[-1]['state'].value,
                        color=self.current_theme["fg"],
                        va='center',
                        fontsize=8
                    )
        
        # Set labels and titles with theme colors
        self.timeline_ax.set_yticks(range(len(threads)))
        self.timeline_ax.set_yticklabels(thread_names, color=self.current_theme["fg"])
        self.timeline_ax.set_xlabel('Time (s)', color=self.current_theme["fg"])
        self.timeline_ax.set_title('Thread Timeline', color=self.current_theme["fg"])
        self.timeline_ax.tick_params(axis='x', colors=self.current_theme["fg"])
        self.timeline_ax.tick_params(axis='y', colors=self.current_theme["fg"])
        
        # Add a grid
        self.timeline_ax.grid(True, linestyle='--', alpha=0.3)
        
        # Adjust axes limits
        self.timeline_ax.set_xlim(0, max(0.1, self.simulator.current_time + 1))
        
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
    
    def _update_performance_visualization(self):
        """Update the performance visualization"""
        try:
            # Get performance stats
            perf_stats = self.simulator.get_performance_stats()
            
            # Update performance treeview
            self.perf_tree.delete(*self.perf_tree.get_children())
            
            # Add thread performance data
            for thread_id, stats in perf_stats['thread_stats'].items():
                self.perf_tree.insert(
                    "", 
                    "end",
                    text=stats['name'],
                    values=(
                        f"{stats['cpu_utilization']:.1f}%",
                        f"{stats['wait_time']:.1f}s",
                        f"{stats['blocked_time']:.1f}s",
                        stats['context_switches']
                    )
                )
            
            # Update overall stats
            self.context_switch_var.set(str(perf_stats['context_switches']))
            self.contention_var.set(str(perf_stats['resource_contentions']))
            self.cpu_util_var.set(f"{perf_stats['overall_cpu_utilization']:.1f}%")
            
            # Clear previous plots
            self.cpu_ax.clear()
            self.event_ax.clear()
            
            # Set titles with theme colors
            self.cpu_ax.set_title('CPU Utilization per Thread', color=self.current_theme["fg"])
            self.event_ax.set_title('Events Timeline', color=self.current_theme["fg"])
            
            # Plot CPU utilization
            thread_names = []
            cpu_utils = []
            
            for thread_id, stats in perf_stats['thread_stats'].items():
                thread_names.append(stats['name'])
                cpu_utils.append(stats['cpu_utilization'])
            
            if thread_names:
                bars = self.cpu_ax.barh(thread_names, cpu_utils, color=self.current_theme["accent"])
                self.cpu_ax.set_xlabel('CPU Utilization (%)', color=self.current_theme["fg"])
                self.cpu_ax.set_xlim(0, 100)
                
                # Add value labels to bars
                for bar in bars:
                    width = bar.get_width()
                    self.cpu_ax.text(
                        width + 1, 
                        bar.get_y() + bar.get_height()/2, 
                        f"{width:.1f}%",
                        va='center', 
                        color=self.current_theme["fg"],
                        fontsize=8
                    )
            
            # Plot recent events on timeline
            events = perf_stats['recent_events']
            if events:
                # Normalize times
                min_time = min(event['time'] for event in events)
                event_times = [(event['time'] - min_time) for event in events]
                event_types = [event['type'] for event in events]
                
                # Use different colors for different event types
                colors = []
                for event_type in event_types:
                    if event_type == 'context_switch':
                        colors.append(self.current_theme["warning"])
                    elif event_type == 'resource_contention':
                        colors.append(self.current_theme["error"])
                    else:
                        colors.append(self.current_theme["accent"])
                
                # Plot events as vertical lines
                for i, (time, color) in enumerate(zip(event_times, colors)):
                    self.event_ax.axvline(
                        x=time, 
                        color=color, 
                        alpha=0.7,
                        linewidth=2
                    )
                
                self.event_ax.set_xlabel('Time (relative)', color=self.current_theme["fg"])
                
                # Add legend
                from matplotlib.lines import Line2D
                legend_elements = [
                    Line2D([0], [0], color=self.current_theme["warning"], lw=2, label='Context Switch'),
                    Line2D([0], [0], color=self.current_theme["error"], lw=2, label='Resource Contention')
                ]
                self.event_ax.legend(handles=legend_elements, loc='upper right')
            
            # Apply theme to axes
            for ax in [self.cpu_ax, self.event_ax]:
                ax.set_facecolor(self.current_theme["bg"])
                ax.spines['bottom'].set_color(self.current_theme["fg"])
                ax.spines['top'].set_color(self.current_theme["fg"])
                ax.spines['right'].set_color(self.current_theme["fg"])
                ax.spines['left'].set_color(self.current_theme["fg"])
                ax.tick_params(axis='x', colors=self.current_theme["fg"])
                ax.tick_params(axis='y', colors=self.current_theme["fg"])
                ax.grid(True, linestyle='--', alpha=0.3)
            
            # Redraw
            self.perf_canvas.draw()
            
        except Exception as e:
            log_exception(e, "Error updating performance visualization")
    
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
        self.speed_label.config(text="1.0x")
        
        # Create an example simulation
        self.simulator.create_example_simulation()
        self.update_ui()
    
    def _on_speed_change(self, event):
        """Handle change in the simulation speed slider"""
        speed = self.speed_var.get()
        self.simulator.set_simulation_speed(speed)
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def _export_data(self):
        """Export simulation data to a file"""
        # Only allow export if we have threads
        if not self.simulator.threads:
            messagebox.showinfo("No Data", "No simulation data to export.")
            return
            
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export Simulation Data"
        )
        
        if not file_path:
            return  # User cancelled
            
        # Export data
        success, result = self.simulator.export_simulation_data(file_path)
        
        if success:
            messagebox.showinfo("Export Successful", f"Simulation data exported to {result}")
        else:
            messagebox.showerror("Export Failed", f"Error exporting data: {result}")
    
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
    
    def _show_about(self):
        """Show about information"""
        about_text = """
Thread Simulator

Version 1.0.0

A visual simulation tool for understanding threading models
and synchronization primitives.

© 2023 Thread Simulator Team
        """
        
        messagebox.showinfo("About Thread Simulator", about_text)
