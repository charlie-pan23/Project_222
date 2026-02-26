'''
Usage Example:
from Utils.Logger import get_logger
logger = get_logger(__name__)

logger.debug("This is a debug message")
logger.info(f"This is an info message: {message}")
'''

# import sys
# from pathlib import Path
# import logging

# root_dir = Path(__file__).resolve().parent.parent
# if str(root_dir) not in sys.path:
#     sys.path.insert(0, str(root_dir))

# class CustomFormatter(logging.Formatter):

#     grey = "\x1b[38;20m"
#     yellow = "\x1b[33;20m"
#     red = "\x1b[31;20m"
#     bold_red = "\x1b[31;1m"
#     blue = "\x1b[34;20m"
#     reset = "\x1b[0m"

#     format_str = "%(asctime)s [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"

#     FORMATS = {
#         logging.DEBUG: grey + format_str + reset,
#         logging.INFO: blue + format_str + reset,
#         logging.WARNING: yellow + format_str + reset,
#         logging.ERROR: red + format_str + reset,
#         logging.CRITICAL: bold_red + format_str + reset
#     }

#     def format(self, record):
#         log_fmt = self.FORMATS.get(record.levelno)
#         formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
#         return formatter.format(record)

# def get_logger(name):
#     logger = logging.getLogger(name)
#     logger.setLevel(logging.DEBUG)

#     if not logger.handlers:
#         ch = logging.StreamHandler()
#         ch.setFormatter(CustomFormatter())
#         logger.addHandler(ch)

#     return logger



import sys
import logging
from pathlib import Path
from collections import deque

# --- GLOBAL LOG BUFFER ---
# This buffer stores the most recent log messages for the Dashboard UI.
# It is shared across all modules that import this Logger.
LOG_BUFFER = deque(maxlen=15)

class CustomFormatter(logging.Formatter):
    """
    Formatter to add colors to the terminal output based on log levels.
    """
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"

    # Default log format string
    format_str = "%(asctime)s [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

class DashboardHandler(logging.Handler):
    """
    A custom logging handler that pushes formatted log messages
    into a global deque buffer for UI rendering.
    """
    def emit(self, record):
        try:
            # Use a simpler format for the UI (no ANSI colors)
            msg = self.format(record)
            LOG_BUFFER.append(msg)
        except Exception:
            self.handleError(record)

def get_logger(name):
    """
    Creates or retrieves a logger instance with dual-handlers:
    1. StreamHandler: Outputs color-coded logs to the standard terminal.
    2. DashboardHandler: Appends logs to the global LOG_BUFFER for the TUI.
    """
    logger = logging.getLogger(name)

    # Set the minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    logger.setLevel(logging.DEBUG)

    # Avoid adding multiple handlers if get_logger is called multiple times
    if not logger.handlers:
        # --- 1. Terminal Handler (Standard Console Output) ---
        ch = logging.StreamHandler()
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)

        # --- 2. Dashboard Handler (UI Buffer Output) ---
        dh = DashboardHandler()
        # Define the visual format for logs appearing inside the Dashboard
        ui_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt='%H:%M:%S'
        )
        dh.setFormatter(ui_formatter)
        logger.addHandler(dh)

    return logger

