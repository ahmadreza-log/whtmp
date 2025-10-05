import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class SettingsManager:
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            # Theme Settings
            "theme": "Light",  # Light, Dark, System
            "program_color": "#2196F3",  # Primary color
            
            # Startup Settings
            "run_on_windows_start": False,
            "start_minimized": False,
            
            # Logging Settings
            "log_directory": "logs",
            "log_filename": "process.log",
            "refresh_interval": 2.0,  # seconds
            
            # UI Settings
            "window_width": 1000,
            "window_height": 700,
            "max_display_processes": 50,
            "max_display_history": 20
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with defaults to handle new settings
                    merged_settings = self.default_settings.copy()
                    merged_settings.update(settings)
                    return merged_settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a setting value and save"""
        self.settings[key] = value
        return self.save_settings()
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()
        return self.save_settings()
    
    def get_log_file_path(self) -> str:
        """Get full path to log file"""
        return os.path.join(self.get("log_directory"), self.get("log_filename"))
    
    def get_theme_mode(self) -> str:
        """Get theme mode for Flet"""
        theme = self.get("theme", "Light")
        if theme == "Dark":
            return "dark"
        elif theme == "Light":
            return "light"
        else:  # System
            return "system"
    
    def get_program_color(self) -> str:
        """Get program primary color"""
        return self.get("program_color", "#2196F3")

# Global settings manager instance
settings_manager = SettingsManager()
