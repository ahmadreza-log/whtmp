import logging
import sys
import traceback
from datetime import datetime
import os
from config import DEBUG_ENABLED, DEBUG_LOG_FILE, DEBUG_CONSOLE_OUTPUT, DEFAULT_LOG_LEVEL, LOG_LEVELS

class DebugLogger:
    def __init__(self):
        self.enabled = DEBUG_ENABLED
        self.logger = None
        self.setup_logger()
    
    def setup_logger(self):
        """Setup logging configuration"""
        if not self.enabled:
            return
        
        # Create logger
        self.logger = logging.getLogger('ProcessMonitor')
        self.logger.setLevel(getattr(logging, DEFAULT_LOG_LEVEL))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        try:
            file_handler = logging.FileHandler(DEBUG_LOG_FILE, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
        
        # Console handler (only in development)
        if DEBUG_CONSOLE_OUTPUT:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, DEFAULT_LOG_LEVEL))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log(self, level, message, exception=None):
        """Log a message with specified level"""
        if not self.enabled or not self.logger:
            return
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        if exception:
            self.logger.log(log_level, f"{message}: {str(exception)}")
            self.logger.log(log_level, traceback.format_exc())
        else:
            self.logger.log(log_level, message)
    
    def debug(self, message):
        """Log debug message"""
        self.log('DEBUG', message)
    
    def info(self, message):
        """Log info message"""
        self.log('INFO', message)
    
    def warning(self, message):
        """Log warning message"""
        self.log('WARNING', message)
    
    def error(self, message, exception=None):
        """Log error message"""
        self.log('ERROR', message, exception)
    
    def critical(self, message, exception=None):
        """Log critical message"""
        self.log('CRITICAL', message, exception)
    
    def log_function_call(self, func_name, args=None, kwargs=None):
        """Log function call for debugging"""
        if not self.enabled:
            return
        
        args_str = str(args) if args else "None"
        kwargs_str = str(kwargs) if kwargs else "None"
        self.debug(f"Function call: {func_name}(args={args_str}, kwargs={kwargs_str})")
    
    def log_exception(self, exception, context=""):
        """Log exception with context"""
        if not self.enabled:
            return
        
        self.error(f"Exception in {context}", exception)
    
    def clear_log(self):
        """Clear debug log file"""
        if not self.enabled:
            return
        
        try:
            if os.path.exists(DEBUG_LOG_FILE):
                with open(DEBUG_LOG_FILE, 'w', encoding='utf-8') as f:
                    f.write("")
                self.info("Debug log cleared")
        except Exception as e:
            print(f"Failed to clear debug log: {e}")

# Global debug logger instance
debug_logger = DebugLogger()

# Convenience functions
def debug(message):
    debug_logger.debug(message)

def info(message):
    debug_logger.info(message)

def warning(message):
    debug_logger.warning(message)

def error(message, exception=None):
    debug_logger.error(message, exception)

def critical(message, exception=None):
    debug_logger.critical(message, exception)

def log_function_call(func_name, args=None, kwargs=None):
    debug_logger.log_function_call(func_name, args, kwargs)

def log_exception(exception, context=""):
    debug_logger.log_exception(exception, context)

def clear_debug_log():
    debug_logger.clear_log()
