"""
Thread Simulator - Main Entry Point
This module initializes and launches the thread simulator application.
"""

import tkinter as tk
import traceback
import sys
import os
import time

# Silence Tk deprecation warning on macOS
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# Import our logger first to ensure it's set up before any other imports
from logger import log_info, log_error, log_exception, log_debug

log_info("Starting Thread Simulator application")

# Try to import ttkthemes for better styling
try:
    from ttkthemes import ThemedTk
    THEMED_TK_AVAILABLE = True
    log_info("ttkthemes package is available")
except ImportError:
    THEMED_TK_AVAILABLE = False
    log_info("ttkthemes package not available, using standard Tk")

# Ensure matplotlib uses the correct backend before any imports
try:
    import matplotlib
    log_info(f"Using matplotlib version {matplotlib.__version__}")
    matplotlib.use('TkAgg')
    log_info("Set matplotlib backend to TkAgg")
except Exception as e:
    log_exception(e, "Failed to configure matplotlib backend")

try:
    from ui import ThreadSimulatorUI
except Exception as e:
    log_exception(e, "Failed to import ThreadSimulatorUI")
    sys.exit(1)

def check_environment():
    """Log information about the execution environment"""
    log_info(f"Python version: {sys.version}")
    log_info(f"Tkinter version: {tk.TkVersion}")
    
    # Check if display is available
    try:
        test_tk = tk.Tk()
        test_tk.withdraw()
        log_info("Display is available and Tkinter is working")
        test_tk.destroy()
    except Exception as e:
        log_exception(e, "Display check failed")

if __name__ == "__main__":
    try:
        # Log environment information
        check_environment()
        
        # Create the main application window
        log_info("Creating main window")
        #root = []
        if THEMED_TK_AVAILABLE:
            # Use ThemedTk for better styling
            root = ThemedTk(theme="arc")
            log_info("Using ThemedTk with 'arc' theme")
        else:
            # Fall back to standard Tk
            root = tk.Tk()
            log_info("Using standard Tk")
            
        root.title("Real Time Multi-Threading Simulator")
        
        # Set application icon if available
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            try:
                icon_img = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon_img)
                log_info("Set application icon")
            except Exception as e:
                log_exception(e, "Failed to set application icon")
        
        # Initialize the UI
        log_info("Initializing UI...")
        app = ThreadSimulatorUI(root)
        log_info("UI initialized successfully")
        
        # Make sure window appears in foreground
        log_debug("Bringing window to foreground")
        root.update()
        #root.deiconify()
        root.lift()
        root.focus_force()
        
        # Start the main event loop
        log_info("Starting main event loop")
        root.mainloop()
    except Exception as e:
        error_msg = log_exception(e, "Application failed to start")
        
        # Show error in a message box if possible
        try:
            import tkinter.messagebox as msgbox
            msgbox.showerror("Error", f"Application failed to start:\n{str(e)}\n\nSee log for details.")
        except Exception as msgbox_error:
            log_exception(msgbox_error, "Failed to show error message box")
        
        sys.exit(1)
