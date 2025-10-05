import flet as ft
import psutil
import json
import time
import threading
from datetime import datetime
import os
import sys
import traceback

from config import (
    DEVELOPMENT_MODE, DEBUG_ENABLED, DATA_FILE, 
    AUTO_REFRESH_INTERVAL, MAX_DISPLAY_PROCESSES, MAX_DISPLAY_HISTORY,
    GUI_TITLE, WINDOW_SIZE, WINDOW_BACKGROUND
)
from settings import settings_manager

class ProcessMonitor:
    def __init__(self):
        self.running_processes = {}
        self.process_history = []
        self.load_data()
        
    def load_data(self):
        """Load existing process data from file"""
        try:
            log_file_path = settings_manager.get_log_file_path()
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            # Try to load from new text format first, then fallback to JSON
            if os.path.exists(log_file_path):
                try:
                    # For now, we'll keep the JSON format for loading existing data
                    # In future versions, we can implement text parsing
                    if os.path.exists(DATA_FILE):
                        with open(DATA_FILE, 'r') as f:
                            data = json.load(f)
                            self.process_history = data.get('history', [])
                            print(f"Loaded {len(self.process_history)} existing records")
                except:
                    self.process_history = []
            else:
                # Try old JSON file as fallback
                if os.path.exists(DATA_FILE):
                    with open(DATA_FILE, 'r') as f:
                        data = json.load(f)
                        self.process_history = data.get('history', [])
                        print(f"Loaded {len(self.process_history)} existing records from old format")
        except Exception as e:
            print(f"Error loading data: {e}")
            self.process_history = []
    
    def save_data(self):
        """Save process data to file in text table format"""
        try:
            log_file_path = settings_manager.get_log_file_path()
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            
            # Create text table format
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 120 + "\n")
                f.write("PROCESS MONITOR LOG\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 120 + "\n\n")
                
                if self.process_history:
                    f.write("PROCESS HISTORY:\n")
                    f.write("-" * 120 + "\n")
                    f.write(f"{'Process Name':<30} {'PID':<8} {'Start Time':<20} {'End Time':<20} {'Duration':<15} {'Status':<10}\n")
                    f.write("-" * 120 + "\n")
                    
                    for record in self.process_history:
                        start_time = datetime.fromisoformat(record['start_time']).strftime('%Y-%m-%d %H:%M:%S')
                        end_time = datetime.fromisoformat(record['end_time']).strftime('%Y-%m-%d %H:%M:%S')
                        duration = record['duration']
                        name = record['name'][:29]  # Truncate if too long
                        
                        f.write(f"{name:<30} {record['pid']:<8} {start_time:<20} {end_time:<20} {duration:<15} {'Completed':<10}\n")
                    
                    f.write("-" * 120 + "\n")
                    f.write(f"Total Records: {len(self.process_history)}\n")
                else:
                    f.write("No process history available.\n")
                
                f.write("\n" + "=" * 120 + "\n")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_current_processes(self):
        """Get currently running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cpu_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'create_time': datetime.fromtimestamp(proc_info['create_time']),
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_mb': proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting processes: {e}")
        return processes
    
    def update_processes(self):
        """Update running processes and detect changes"""
        current_processes = self.get_current_processes()
        current_pids = {p['pid'] for p in current_processes}
        previous_pids = set(self.running_processes.keys())
        
        # New processes
        new_pids = current_pids - previous_pids
        for pid in new_pids:
            proc = next(p for p in current_processes if p['pid'] == pid)
            self.running_processes[pid] = {
                'name': proc['name'],
                'start_time': proc['create_time'],
                'pid': pid
            }
            print(f"Process started: {proc['name']} (PID: {pid})")
        
        # Ended processes
        ended_pids = previous_pids - current_pids
        for pid in ended_pids:
            proc_info = self.running_processes[pid]
            end_time = datetime.now()
            
            # Add to history
            self.process_history.append({
                'name': proc_info['name'],
                'pid': pid,
                'start_time': proc_info['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration': str(end_time - proc_info['start_time'])
            })
            
            print(f"Process ended: {proc_info['name']} (PID: {pid})")
            del self.running_processes[pid]
        
        # Save data
        self.save_data()
        
        return current_processes

class ModernProcessMonitorApp:
    def __init__(self):
        self.monitor = ProcessMonitor()
        self.page = None
        self.monitoring_thread = None
        self.is_monitoring = False
        self.auto_refresh_interval = settings_manager.get("refresh_interval", AUTO_REFRESH_INTERVAL)
        
        # UI Controls
        self.process_grid = None
        self.history_grid = None
        self.stats_text = None
        self.start_button = None
        self.stop_button = None
        self.refresh_button = None
        self.status_indicator = None
        
    def create_control_panel(self):
        """Create control panel with modern buttons"""
        self.start_button = ft.ElevatedButton(
            "Start",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self.start_monitoring,
            visible=not self.is_monitoring
        )
        
        self.stop_button = ft.ElevatedButton(
            "Stop",
            icon=ft.Icons.STOP,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self.stop_monitoring,
            visible=self.is_monitoring
        )
        
        self.refresh_button = ft.ElevatedButton(
            "Refresh",
            icon=ft.Icons.REFRESH,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=self.refresh_data
        )
        
        self.status_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=12, color=ft.Colors.GREEN if self.is_monitoring else ft.Colors.GREY),
                ft.Text(
                    "Running" if self.is_monitoring else "Stopped",
                    color=ft.Colors.GREEN if self.is_monitoring else ft.Colors.GREY,
                    weight=ft.FontWeight.BOLD,
                    size=14
                )
            ]),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=15,
            border=ft.border.all(1, ft.Colors.GREEN_200 if self.is_monitoring else ft.Colors.GREY_300)
        )
        
        return ft.Container(
            content=ft.Row([
                self.start_button,
                self.stop_button,
                self.refresh_button,
                ft.Container(expand=True),
                self.status_indicator
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(12),
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_process_card(self, process):
        """Create a compact process card"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.DASHBOARD,
                            color=ft.Colors.BLUE_600,
                            size=16
                        ),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=ft.padding.all(6),
                        border_radius=6
                    ),
                    ft.Column([
                        ft.Text(
                            process['name'][:18] + "..." if len(process['name']) > 18 else process['name'],
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800
                        ),
                        ft.Text(
                            f"PID: {process['pid']}",
                            size=10,
                            color=ft.Colors.GREY_600
                        )
                    ], expand=True),
                    ft.Column([
                        ft.Text(
                            f"{process['cpu_percent']:.1f}%",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_600
                        ),
                        ft.Text(
                            "CPU",
                            size=8,
                            color=ft.Colors.GREY_600
                        )
                    ]),
                    ft.Column([
                        ft.Text(
                            f"{process['memory_mb']:.1f}MB",
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_600
                        ),
                        ft.Text(
                            "RAM",
                            size=8,
                            color=ft.Colors.GREY_600
                        )
                    ])
                ], spacing=6),
            ], spacing=2),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(6),
            border_radius=6,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=2,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 1)
            ),
            height=70,
            width=220
        )
    
    def create_history_card(self, record):
        """Create a compact history card"""
        start_time = datetime.fromisoformat(record['start_time'])
        end_time = datetime.fromisoformat(record['end_time'])
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.HISTORY,
                            color=ft.Colors.PURPLE_600,
                            size=16
                        ),
                        bgcolor=ft.Colors.PURPLE_50,
                        padding=ft.padding.all(6),
                        border_radius=6
                    ),
                    ft.Column([
                        ft.Text(
                            record['name'][:18] + "..." if len(record['name']) > 18 else record['name'],
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800
                        ),
                        ft.Text(
                            f"PID: {record['pid']}",
                            size=10,
                            color=ft.Colors.GREY_600
                        )
                    ], expand=True),
                    ft.Column([
                        ft.Text(
                            record['duration'].split('.')[0],  # Remove microseconds
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_600
                        ),
                        ft.Text(
                            "Duration",
                            size=8,
                            color=ft.Colors.GREY_600
                        )
                    ])
                ], spacing=6),
                ft.Row([
                    ft.Text(
                        f"Start: {start_time.strftime('%H:%M:%S')}",
                        size=9,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        f"End: {end_time.strftime('%H:%M:%S')}",
                        size=9,
                        color=ft.Colors.GREY_600
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=2),
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.all(6),
            border_radius=6,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=2,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 1)
            ),
            height=80,
            width=220
        )
    
    def create_responsive_grid(self, controls):
        """Create responsive grid layout with flex"""
        # Create a single row with all controls that will wrap automatically
        return ft.Row(
            controls,
            spacing=8,
            wrap=True,
            alignment=ft.MainAxisAlignment.START,
            run_spacing=8
        )
    
    def create_settings_tab(self):
        """Create settings tab with all configuration options"""
        # Theme Settings
        theme_dropdown = ft.Dropdown(
            label="Program Theme",
            hint_text="Choose your preferred theme",
            value=settings_manager.get("theme"),
            options=[
                ft.dropdown.Option("Light", "Light Theme"),
                ft.dropdown.Option("Dark", "Dark Theme"),
                ft.dropdown.Option("System", "Follow System Theme")
            ],
            on_change=self.on_theme_change,
            width=300
        )
        
        # Color Picker
        color_picker = ft.TextField(
            label="Program Color",
            hint_text="Hex color code (e.g., #2196F3)",
            value=settings_manager.get("program_color"),
            on_change=self.on_color_change,
            width=300
        )
        
        # Startup Settings
        auto_start_switch = ft.Switch(
            label="Run When Windows Starts",
            value=settings_manager.get("run_on_windows_start"),
            on_change=self.on_auto_start_change
        )
        
        start_minimized_switch = ft.Switch(
            label="Start Minimized (if auto-start is enabled)",
            value=settings_manager.get("start_minimized"),
            on_change=self.on_start_minimized_change
        )
        
        # Log Settings
        log_directory_field = ft.TextField(
            label="Log Directory",
            hint_text="Directory for log files",
            value=settings_manager.get("log_directory"),
            on_change=self.on_log_directory_change,
            width=300
        )
        
        log_filename_field = ft.TextField(
            label="Log Filename",
            hint_text="Name of the log file",
            value=settings_manager.get("log_filename"),
            on_change=self.on_log_filename_change,
            width=300
        )
        
        # Refresh Interval
        refresh_interval_field = ft.TextField(
            label="Refresh Interval (seconds)",
            hint_text="How often to refresh process data",
            value=str(settings_manager.get("refresh_interval")),
            on_change=self.on_refresh_interval_change,
            width=300
        )
        
        # Reset Button
        reset_button = ft.ElevatedButton(
            "Reset to Defaults",
            icon=ft.Icons.RESTORE,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE_600,
                color=ft.Colors.WHITE
            ),
            on_click=self.reset_settings
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Application Settings",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_800
                ),
                
                ft.Divider(),
                
                # Theme Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Theme Settings", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Customize the appearance of the application", size=12, color=ft.Colors.GREY_600),
                        theme_dropdown,
                        color_picker
                    ], spacing=8),
                    padding=ft.padding.all(16),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.BLUE_200)
                ),
                
                # Startup Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Startup Settings", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Configure how the application starts with Windows", size=12, color=ft.Colors.GREY_600),
                        auto_start_switch,
                        start_minimized_switch
                    ], spacing=8),
                    padding=ft.padding.all(16),
                    bgcolor=ft.Colors.GREEN_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREEN_200)
                ),
                
                # Logging Section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Logging Settings", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("Configure where and how process data is logged", size=12, color=ft.Colors.GREY_600),
                        log_directory_field,
                        log_filename_field,
                        refresh_interval_field
                    ], spacing=8),
                    padding=ft.padding.all(16),
                    bgcolor=ft.Colors.PURPLE_50,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.PURPLE_200)
                ),
                
                # Actions
                ft.Row([
                    reset_button,
                    ft.Container(expand=True)
                ], alignment=ft.MainAxisAlignment.START)
                
            ], spacing=16, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(16)
        )
    
    def create_tabs(self):
        """Create responsive tabs"""
        return ft.Tabs(
            selected_index=0,
            animation_duration=200,
            tabs=[
                ft.Tab(
                    text="Processes",
                    icon=ft.Icons.LIST_ALT,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Running Processes",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_800
                            ),
                            ft.Container(
                                content=ft.ListView(
                                    controls=[self.process_grid],
                                    spacing=8,
                                    padding=ft.padding.all(8),
                                    auto_scroll=False,
                                    expand=True
                                ),
                                height=400,
                                border=ft.border.all(1, ft.Colors.GREY_200),
                                border_radius=8
                            )
                        ]),
                        padding=ft.padding.all(16)
                    )
                ),
                ft.Tab(
                    text="History",
                    icon=ft.Icons.HISTORY,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Process History",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_800
                            ),
                            ft.Container(
                                content=ft.ListView(
                                    controls=[self.history_grid],
                                    spacing=8,
                                    padding=ft.padding.all(8),
                                    auto_scroll=False,
                                    expand=True
                                ),
                                height=400,
                                border=ft.border.all(1, ft.Colors.GREY_200),
                                border_radius=8
                            )
                        ]),
                        padding=ft.padding.all(16)
                    )
                ),
                ft.Tab(
                    text="Stats",
                    icon=ft.Icons.ANALYTICS,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "System Statistics",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_800
                            ),
                            ft.Container(
                                content=self.stats_text,
                                padding=ft.padding.all(16),
                                bgcolor=ft.Colors.GREY_50,
                                border_radius=8,
                                border=ft.border.all(1, ft.Colors.GREY_200)
                            )
                        ]),
                        padding=ft.padding.all(16)
                    )
                ),
                ft.Tab(
                    text="Settings",
                    icon=ft.Icons.SETTINGS,
                    content=self.create_settings_tab()
                )
            ],
            expand=True
        )
    
    def create_ui(self, page: ft.Page):
        """Create the main UI"""
        self.page = page
        
        # Set page properties
        page.title = GUI_TITLE
        theme_mode = settings_manager.get_theme_mode()
        page.theme_mode = getattr(ft.ThemeMode, theme_mode.upper())
        page.window_width = settings_manager.get("window_width", 1000)
        page.window_height = settings_manager.get("window_height", 700)
        page.window_min_width = 800
        page.window_min_height = 600
        page.padding = 0
        page.bgcolor = ft.Colors.GREY_100
        
        # Set Poppins font
        page.fonts = {
            "Poppins": "https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap"
        }
        page.theme = ft.Theme(font_family="Poppins")
        page.update()
        
        # Initialize UI controls
        self.process_grid = ft.Row([], spacing=8, wrap=True, run_spacing=8)
        self.history_grid = ft.Row([], spacing=8, wrap=True, run_spacing=8)
        
        self.stats_text = ft.Text(
            "Click 'Start' to begin monitoring processes.",
            size=14,
            color=ft.Colors.GREY_600
        )
        
        # Create main layout
        main_content = ft.Column([
            ft.Container(
                content=self.create_control_panel(),
                margin=ft.margin.all(12)
            ),
            ft.Container(
                content=self.create_tabs(),
                expand=True,
                margin=ft.margin.symmetric(horizontal=12),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=ft.Colors.BLACK26,
                    offset=ft.Offset(0, 5)
                )
            )
        ], expand=True)
        
        page.add(main_content)
        
        # Initial data load
        self.refresh_data()
    
    def start_monitoring(self, e):
        """Start process monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitoring_thread.start()
            self.update_buttons()
            print("Monitoring started")
    
    def stop_monitoring(self, e):
        """Stop process monitoring"""
        self.is_monitoring = False
        self.update_buttons()
        print("Monitoring stopped")
    
    def update_buttons(self):
        """Update button states and status indicator"""
        try:
            if self.start_button:
                self.start_button.visible = not self.is_monitoring
            if self.stop_button:
                self.stop_button.visible = self.is_monitoring
            if self.status_indicator:
                # Update status indicator
                status_content = ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, size=12, color=ft.Colors.GREEN if self.is_monitoring else ft.Colors.GREY),
                    ft.Text(
                        "Running" if self.is_monitoring else "Stopped",
                        color=ft.Colors.GREEN if self.is_monitoring else ft.Colors.GREY,
                        weight=ft.FontWeight.BOLD,
                        size=14
                    )
                ])
                self.status_indicator.content = status_content
                self.status_indicator.border = ft.border.all(1, ft.Colors.GREEN_200 if self.is_monitoring else ft.Colors.GREY_300)
            
            self.update_ui()
        except Exception as e:
            print(f"Error updating buttons: {e}")
    
    def refresh_data(self, e=None):
        """Refresh all data"""
        try:
            # Update processes
            current_processes = self.monitor.update_processes()
            
            # Update process grid
            process_cards = []
            for process in current_processes[:MAX_DISPLAY_PROCESSES]:
                process_cards.append(self.create_process_card(process))
            self.process_grid.controls = process_cards
            
            # Update history grid
            history_cards = []
            for record in self.monitor.process_history[-MAX_DISPLAY_HISTORY:]:
                history_cards.append(self.create_history_card(record))
            self.history_grid.controls = history_cards
            
            # Update statistics
            total_processes = len(current_processes)
            total_history = len(self.monitor.process_history)
            running_count = len(self.monitor.running_processes)
            
            self.stats_text.value = f"""
📊 System Statistics

🔄 Running Processes: {total_processes}
📈 Tracked Processes: {running_count}
📋 History Records: {total_history}
⏰ Last Updated: {datetime.now().strftime('%H:%M:%S')}

💾 Data File: {DATA_FILE}
🔧 Status: {'Active' if self.is_monitoring else 'Stopped'}
            """.strip()
            
            self.update_ui()
            
        except Exception as e:
            print(f"Error refreshing data: {e}")
            traceback.print_exc()
    
    def monitor_loop(self):
        """Background monitoring loop"""
        while self.is_monitoring:
            try:
                self.refresh_data()
                time.sleep(self.auto_refresh_interval)
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                traceback.print_exc()
                break
    
    def update_ui(self):
        """Update UI controls"""
        try:
            if self.page:
                self.page.update()
        except Exception as e:
            print(f"Error updating UI: {e}")
    
    # Settings event handlers
    def on_theme_change(self, e):
        """Handle theme change"""
        settings_manager.set("theme", e.control.value)
        # Apply theme immediately
        theme_mode = settings_manager.get_theme_mode()
        self.page.theme_mode = getattr(ft.ThemeMode, theme_mode.upper())
        self.page.update()
    
    def on_color_change(self, e):
        """Handle color change"""
        color = e.control.value
        if color and color.startswith('#'):
            settings_manager.set("program_color", color)
    
    def on_auto_start_change(self, e):
        """Handle auto-start change"""
        settings_manager.set("run_on_windows_start", e.control.value)
        # TODO: Implement Windows startup integration
    
    def on_start_minimized_change(self, e):
        """Handle start minimized change"""
        settings_manager.set("start_minimized", e.control.value)
    
    def on_log_directory_change(self, e):
        """Handle log directory change"""
        settings_manager.set("log_directory", e.control.value)
    
    def on_log_filename_change(self, e):
        """Handle log filename change"""
        settings_manager.set("log_filename", e.control.value)
    
    def on_refresh_interval_change(self, e):
        """Handle refresh interval change"""
        try:
            interval = float(e.control.value)
            if interval > 0:
                settings_manager.set("refresh_interval", interval)
                self.auto_refresh_interval = interval
        except ValueError:
            pass  # Invalid input, ignore
    
    def reset_settings(self, e):
        """Reset all settings to defaults"""
        settings_manager.reset_to_defaults()
        # Refresh the page to show default values
        self.page.go("/")
        self.page.update()

def main(page: ft.Page):
    """Main application entry point"""
    try:
        app = ModernProcessMonitorApp()
        app.create_ui(page)
    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()
        page.add(ft.Text(f"Error: {e}", color=ft.Colors.RED))

if __name__ == "__main__":
    try:
        ft.app(target=main, view=ft.AppView.FLET_APP)
    except Exception as e:
        print(f"Failed to start application: {e}")
        traceback.print_exc()