# Modern Process Monitor Configuration

# Development/Production mode
DEVELOPMENT_MODE = True  # Set to False for production

# Debug settings
DEBUG_ENABLED = DEVELOPMENT_MODE
DEBUG_LOG_FILE = "debug.log"
DEBUG_CONSOLE_OUTPUT = DEVELOPMENT_MODE

# Application settings
CHECK_INTERVAL = 2  # seconds
DATA_FILE = "process_log.json"
GUI_TITLE = "Modern Process Monitor"

# GUI settings
WINDOW_SIZE = "1000x700"
WINDOW_BACKGROUND = "#f5f5f5"
AUTO_REFRESH_INTERVAL = 2.0
MAX_DISPLAY_PROCESSES = 50
MAX_DISPLAY_HISTORY = 20

# Process filtering
EXCLUDE_SYSTEM_PROCESSES = True
MIN_PID = 0

# Logging levels
LOG_LEVELS = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4
}

# Default log level
DEFAULT_LOG_LEVEL = 'INFO' if DEVELOPMENT_MODE else 'WARNING'
