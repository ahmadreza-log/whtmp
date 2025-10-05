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

class ProcessMonitor:
    def __init__(self):
        self.running_processes = {}
        self.process_history = []
        self.load_data()
        
    def load_data(self):
        """Load existing process data from file"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.process_history = data.get('history', [])
                    print(f"Loaded {len(self.process_history)} existing records")
        except Exception as e:
            print(f"Error loading data: {e}")
            self.process_history = []
    
    def save_data(self):
        """Save process data to file"""
        try:
            data = {
                'history': self.process_history,
                'last_updated': datetime.now().isoformat()
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
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
        self.auto_refresh_interval = AUTO_REFRESH_INTERVAL
        
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
                )
            ],
            expand=True
        )
    
    def create_ui(self, page: ft.Page):
        """Create the main UI"""
        self.page = page
        
        # Set page properties
        page.title = GUI_TITLE
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_width = 1000
        page.window_height = 700
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