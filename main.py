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
                f.write("=" * 140 + "\n")
                f.write("PROCESS MONITOR LOG\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 140 + "\n\n")
                
                if self.process_history:
                    f.write("PROCESS HISTORY:\n")
                    f.write("-" * 120 + "\n")
                    f.write(f"{'Process Name':<30} {'PID':<8} {'Start Date':<12} {'Start Time':<10} {'End Date':<12} {'End Time':<10} {'Duration':<15} {'Status':<10}\n")
                    f.write("-" * 140 + "\n")
                    
                    for record in self.process_history:
                        start_dt = datetime.fromisoformat(record['start_time'])
                        end_dt = datetime.fromisoformat(record['end_time'])
                        start_date = start_dt.strftime('%Y-%m-%d')
                        start_time = start_dt.strftime('%H:%M:%S')
                        end_date = end_dt.strftime('%Y-%m-%d')
                        end_time = end_dt.strftime('%H:%M:%S')
                        duration = record['duration']
                        name = record['name'][:29]  # Truncate if too long
                        
                        f.write(f"{name:<30} {record['pid']:<8} {start_date:<12} {start_time:<10} {end_date:<12} {end_time:<10} {duration:<15} {'Completed':<10}\n")
                    
                    f.write("-" * 140 + "\n")
                    f.write(f"Total Records: {len(self.process_history)}\n")
                else:
                    f.write("No process history available.\n")
                
                f.write("\n" + "=" * 140 + "\n")
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
                'start_time': datetime.now(),  # Use current time instead of system create_time
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
        theme_mode = settings_manager.get_theme_mode()
        
        # Theme-based colors for control panel
        if theme_mode == "dark":
            panel_bg = ft.Colors.GREY_800
            status_bg = ft.Colors.GREY_700
            shadow_color = ft.Colors.BLACK54
        else:
            panel_bg = ft.Colors.WHITE
            status_bg = ft.Colors.WHITE
            shadow_color = ft.Colors.BLACK12
        
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
            bgcolor=status_bg,
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
            bgcolor=panel_bg,
            padding=ft.padding.all(12),
            border_radius=8,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=shadow_color,
                offset=ft.Offset(0, 2)
            )
        )
    
    def create_process_card(self, process):
        """Create a compact process card"""
        theme_mode = settings_manager.get_theme_mode()
        
        # Theme-based colors
        if theme_mode == "dark":
            bg_color = ft.Colors.GREY_800
            text_color = ft.Colors.WHITE
            secondary_text_color = ft.Colors.GREY_300
            border_color = ft.Colors.GREY_600
            icon_bg = ft.Colors.BLUE_900
            shadow_color = ft.Colors.BLACK54
        else:
            bg_color = ft.Colors.WHITE
            text_color = ft.Colors.GREY_800
            secondary_text_color = ft.Colors.GREY_600
            border_color = ft.Colors.GREY_200
            icon_bg = ft.Colors.BLUE_50
            shadow_color = ft.Colors.BLACK12
        
        # Calculate runtime since monitoring started
        if process['pid'] in self.monitor.running_processes:
            start_time = self.monitor.running_processes[process['pid']]['start_time']
        else:
            start_time = datetime.now()  # Fallback for processes not in our tracking
            
        runtime = datetime.now() - start_time
        total_seconds = int(runtime.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            runtime_str = f"{days}d {hours:02d}h {minutes:02d}m {seconds:02d}s"
        elif hours > 0:
            runtime_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        elif minutes > 0:
            runtime_str = f"{minutes:02d}m {seconds:02d}s"
        else:
            runtime_str = f"{seconds:02d}s"
        
        # Format memory
        memory_str = f"{process['memory_mb']:.1f} MB"
        if process['memory_mb'] > 1024:
            memory_str = f"{process['memory_mb']/1024:.1f} GB"
        
        return ft.Container(
            content=ft.Column([
                # Header with icon and name
                ft.Row([
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.DASHBOARD,
                            color=ft.Colors.BLUE_600,
                            size=18
                        ),
                        bgcolor=icon_bg,
                        padding=ft.padding.all(8),
                        border_radius=8
                    ),
                    ft.Column([
                        ft.Text(
                            process['name'][:20] + "..." if len(process['name']) > 20 else process['name'],
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=text_color
                        ),
                        ft.Text(
                            f"PID: {process['pid']}",
                            size=11,
                            color=secondary_text_color
                        )
                    ], expand=True, spacing=2)
                ], spacing=8),
                
                ft.Divider(height=1, color=border_color),
                
                # Stats grid
                ft.Column([
                    # First row - CPU and Memory
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    f"{min(process['cpu_percent'], 100):.1f}%",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.ORANGE_600
                                ),
                                ft.Text("CPU", size=9, color=secondary_text_color)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                            expand=True,
                            padding=ft.padding.all(6),
                            bgcolor=icon_bg if theme_mode == "dark" else ft.Colors.ORANGE_50,
                            border_radius=6
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    memory_str,
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN_600
                                ),
                                ft.Text("Memory", size=9, color=secondary_text_color)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                            expand=True,
                            padding=ft.padding.all(6),
                            bgcolor=icon_bg if theme_mode == "dark" else ft.Colors.GREEN_50,
                            border_radius=6
                        )
                    ], spacing=6),
                    
                    # Second row - Runtime and Start Time
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    runtime_str,
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.PURPLE_600
                                ),
                                ft.Text("Runtime", size=9, color=secondary_text_color)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                            expand=True,
                            padding=ft.padding.all(6),
                            bgcolor=icon_bg if theme_mode == "dark" else ft.Colors.PURPLE_50,
                            border_radius=6
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    start_time.strftime('%H:%M:%S'),
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.TEAL_600
                                ),
                                ft.Text("Started", size=9, color=secondary_text_color)
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=1),
                            expand=True,
                            padding=ft.padding.all(6),
                            bgcolor=icon_bg if theme_mode == "dark" else ft.Colors.TEAL_50,
                            border_radius=6
                        )
                    ], spacing=6)
                ], spacing=6)
            ], spacing=8),
            width=280,
            padding=ft.padding.all(16),
            bgcolor=bg_color,
            border_radius=16,
            border=ft.border.all(1, border_color),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=shadow_color,
                offset=ft.Offset(0, 4)
            )
        )
    
    def create_history_card(self, record):
        """Create a compact history card"""
        start_time = datetime.fromisoformat(record['start_time'])
        end_time = datetime.fromisoformat(record['end_time'])
        
        theme_mode = settings_manager.get_theme_mode()
        
        # Theme-based colors
        if theme_mode == "dark":
            bg_color = ft.Colors.GREY_800
            text_color = ft.Colors.WHITE
            secondary_text_color = ft.Colors.GREY_300
            border_color = ft.Colors.GREY_600
            icon_bg = ft.Colors.PURPLE_900
            shadow_color = ft.Colors.BLACK54
        else:
            bg_color = ft.Colors.WHITE
            text_color = ft.Colors.GREY_800
            secondary_text_color = ft.Colors.GREY_600
            border_color = ft.Colors.GREY_200
            icon_bg = ft.Colors.PURPLE_50
            shadow_color = ft.Colors.BLACK12
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.HISTORY,
                            color=ft.Colors.PURPLE_600,
                            size=16
                        ),
                        bgcolor=icon_bg,
                        padding=ft.padding.all(6),
                        border_radius=6
                    ),
                    ft.Column([
                        ft.Text(
                            record['name'][:18] + "..." if len(record['name']) > 18 else record['name'],
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color=text_color
                        ),
                        ft.Text(
                            f"PID: {record['pid']}",
                            size=10,
                            color=secondary_text_color
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
                            color=secondary_text_color
                        )
                    ])
                ], spacing=6),
                ft.Row([
                    ft.Text(
                        f"Start: {start_time.strftime('%H:%M:%S')}",
                        size=9,
                        color=secondary_text_color
                    ),
                    ft.Text(
                        f"End: {end_time.strftime('%H:%M:%S')}",
                        size=9,
                        color=secondary_text_color
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=2),
            bgcolor=bg_color,
            padding=ft.padding.all(6),
            border_radius=6,
            border=ft.border.all(1, border_color),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=2,
                color=shadow_color,
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
        # Theme Settings - Removed as requested
        
        # Color Selection - Removed as requested
        
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
        log_directory_button = ft.ElevatedButton(
            f"📁 {settings_manager.get('log_directory')}",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self.open_directory_picker,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_100,
                color=ft.Colors.BLUE_800
            )
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
        
        theme_mode = settings_manager.get_theme_mode()
        
        # Theme-based colors
        if theme_mode == "dark":
            bg_color = ft.Colors.GREY_900
            text_color = ft.Colors.WHITE
            secondary_text_color = ft.Colors.GREY_300
        else:
            bg_color = ft.Colors.WHITE
            text_color = ft.Colors.GREY_800
            secondary_text_color = ft.Colors.GREY_600
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Application Settings",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=text_color
                ),
                
                ft.Divider(),
                
                # All settings in single column
                # Theme and color settings removed as requested
                
                ft.Text("Run When Windows Starts", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text("Automatically start the application when Windows boots", size=12, color=secondary_text_color),
                auto_start_switch,
                
                ft.Text("Start Minimized", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text("Start the application minimized if auto-start is enabled", size=12, color=secondary_text_color),
                start_minimized_switch,
                
                ft.Text("Log Directory", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text("Directory where log files will be stored", size=12, color=secondary_text_color),
                log_directory_button,
                
                ft.Text("Log Filename", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text("Name of the main log file", size=12, color=secondary_text_color),
                log_filename_field,
                
                ft.Text("Refresh Interval", size=16, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Text("How often to refresh process data (in seconds)", size=12, color=secondary_text_color),
                refresh_interval_field,
                
                # Actions
                ft.Row([
                    reset_button,
                    ft.Container(expand=True)
                ], alignment=ft.MainAxisAlignment.START)
                
            ], spacing=16, scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(16),
            bgcolor=bg_color
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
        
        # Calculate optimal width for 4 cards
        # Card width: 220px, spacing: 8px, padding: 16px * 2, margin: 12px * 2
        optimal_width = (220 * 4) + (8 * 3) + (16 * 2) + (12 * 2)  # ~940px
        
        # Set page properties
        page.title = GUI_TITLE
        theme_mode = settings_manager.get_theme_mode()
        page.theme_mode = getattr(ft.ThemeMode, theme_mode.upper())
        page.window_width = optimal_width
        page.window_height = settings_manager.get("window_height", 700)
        page.window_min_width = 800
        page.window_min_height = 600
        page.padding = 0
        
        # Set theme-based background
        if theme_mode == "dark":
            page.bgcolor = ft.Colors.GREY_900
        else:
            page.bgcolor = ft.Colors.GREY_100
        
        # Apply theme colors to main container
        self.current_theme = theme_mode
        
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
        
        # Create main layout with theme-aware colors
        main_bg_color = ft.Colors.GREY_900 if theme_mode == "dark" else ft.Colors.WHITE
        main_shadow_color = ft.Colors.BLACK54 if theme_mode == "dark" else ft.Colors.BLACK26
        
        main_content = ft.Column([
            ft.Container(
                content=self.create_control_panel(),
                margin=ft.margin.all(12)
            ),
            ft.Container(
                content=self.create_tabs(),
                expand=True,
                margin=ft.margin.symmetric(horizontal=12),
                bgcolor=main_bg_color,
                border_radius=12,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=15,
                    color=main_shadow_color,
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
    # Theme change functionality removed as requested
    
    # Color change functionality removed as requested
    
    def close_dialog(self, e):
        """Close the dialog"""
        self.page.dialog.open = False
        self.page.update()
    
    def on_auto_start_change(self, e):
        """Handle auto-start change"""
        settings_manager.set("run_on_windows_start", e.control.value)
        # TODO: Implement Windows startup integration
    
    def on_start_minimized_change(self, e):
        """Handle start minimized change"""
        settings_manager.set("start_minimized", e.control.value)
    
    def open_directory_picker(self, e):
        """Open directory picker dialog using Flet"""
        def on_result(result: ft.FilePickerResultEvent):
            if result.path:
                settings_manager.set("log_directory", result.path)
                # Update button text
                e.control.text = f"📁 {result.path}"
                self.page.update()
        
        # Create file picker for directory selection
        file_picker = ft.FilePicker(
            on_result=on_result,
        )
        self.page.overlay.append(file_picker)
        self.page.update()
        
        # Open directory picker
        file_picker.get_directory_path(
            dialog_title="Select Log Directory",
            initial_directory=settings_manager.get("log_directory")
        )
    
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
                # Restart monitoring with new interval if currently monitoring
                if self.is_monitoring:
                    self.stop_monitoring()
                    time.sleep(0.1)  # Brief pause
                    self.start_monitoring()
        except ValueError:
            pass  # Invalid input, ignore
    
    def reset_settings(self, e):
        """Reset all settings to defaults"""
        settings_manager.reset_to_defaults()
        # Update auto refresh interval
        self.auto_refresh_interval = settings_manager.get("refresh_interval", AUTO_REFRESH_INTERVAL)
        # Restart monitoring with new interval if currently monitoring
        if self.is_monitoring:
            self.stop_monitoring()
            time.sleep(0.1)  # Brief pause
            self.start_monitoring()
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