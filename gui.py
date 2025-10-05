import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import json
import time
import threading
from datetime import datetime
import os
import sys
import traceback
from config import DEVELOPMENT_MODE, DEBUG_ENABLED, GUI_TITLE, WINDOW_SIZE, WINDOW_BACKGROUND
from debug import debug, info, warning, error, critical, log_exception, clear_debug_log
from ui_kit import ui_kit

class ProcessMonitorGUI:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title(GUI_TITLE)
            self.root.geometry(WINDOW_SIZE)
            self.root.configure(bg=WINDOW_BACKGROUND)
            
            # Set up error handling
            self.setup_error_handling()
            
            info("GUI initialization started")
            
            # Process monitoring variables
            self.running_processes = {}
            self.process_history = []
            self.monitoring = False
            self.check_interval = 2
            self.log_file = "process_log.json"
            
            # Load existing log
            self.load_existing_log()
            
            # Start monitoring thread
            self.monitor_thread = None
            
            # Auto-refresh settings
            self.auto_refresh_enabled = True
            self.auto_refresh_interval = 1000  # milliseconds
            self.auto_refresh_job = None
            
            # Create GUI
            self.create_widgets()
            
            info("GUI initialization completed successfully")
            
        except Exception as e:
            error("Failed to initialize GUI", e)
            messagebox.showerror("Initialization Error", 
                               f"Failed to initialize GUI:\n{str(e)}\n\nCheck debug.log for details.")
            sys.exit(1)
    
    def setup_error_handling(self):
        """Setup global error handling"""
        if DEBUG_ENABLED:
            # Redirect stderr to debug logger
            class DebugStderr:
                def write(self, message):
                    if message.strip():
                        error(f"STDERR: {message.strip()}")
                
                def flush(self):
                    pass
            
            sys.stderr = DebugStderr()
    
    def load_existing_log(self):
        """Load existing process history from log file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.process_history = data.get('process_history', [])
            except Exception as e:
                print(f"Error loading existing log: {e}")
                self.process_history = []
    
    def save_log(self):
        """Save current process history to log file"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'process_history': self.process_history
            }
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving log: {e}")
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame with modern styling
        main_frame = ui_kit.create_modern_frame(self.root, 'Main.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header frame
        header_frame = ui_kit.create_modern_frame(main_frame, 'Header.TFrame')
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Title
        title_label = ui_kit.create_modern_label(header_frame, "🖥️ Windows Process Monitor", 'Title.TLabel')
        title_label.pack(pady=15)
        
        # Control buttons frame
        control_frame = ui_kit.create_modern_frame(main_frame, 'Card.TFrame')
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10, padx=10)
        
        # Start/Stop button
        self.start_button = ui_kit.create_modern_button(button_frame, "🚀 Start Monitoring", 
                                                       'Primary.TButton', self.toggle_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save button
        save_button = ui_kit.create_modern_button(button_frame, "💾 Save Log", 
                                                 'Info.TButton', self.save_log)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Auto-refresh toggle
        self.auto_refresh_button = ui_kit.create_modern_button(button_frame, "⏰ Auto Refresh: ON", 
                                                              'Success.TButton', self.toggle_auto_refresh)
        self.auto_refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status frame
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Status label
        self.status_label = ui_kit.create_modern_label(status_frame, "Status: Stopped", 'Status.TLabel')
        self.status_label.pack()
        
        # Notebook for tabs with modern styling
        self.notebook = ui_kit.create_modern_notebook(main_frame)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Current Processes Tab
        self.create_current_processes_tab()
        
        # Process History Tab
        self.create_history_tab()
        
        # Statistics Tab
        self.create_statistics_tab()
        
        # Log Tab
        self.create_log_tab()
        
        # Debug Tab (only in development mode)
        if DEVELOPMENT_MODE:
            self.create_debug_tab()
        
        # Start auto-refresh
        self.start_auto_refresh()
        
        # Initial refresh
        self.refresh_processes()
    
    def create_current_processes_tab(self):
        """Create current processes tab"""
        current_frame = ui_kit.create_modern_frame(self.notebook, 'Main.TFrame')
        self.notebook.add(current_frame, text="📋 Current Processes")
        
        # Treeview for processes with modern styling
        columns = ('Process Name', 'PID', 'Start Time', 'Duration')
        self.process_tree = ui_kit.create_modern_treeview(current_frame, columns)
        
        # Configure columns
        self.process_tree.column('Process Name', width=250, anchor='w')
        self.process_tree.column('PID', width=80, anchor='center')
        self.process_tree.column('Start Time', width=180, anchor='center')
        self.process_tree.column('Duration', width=120, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(current_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    def create_history_tab(self):
        """Create process history tab"""
        history_frame = ui_kit.create_modern_frame(self.notebook, 'Main.TFrame')
        self.notebook.add(history_frame, text="📊 Process History")
        
        # Treeview for history with modern styling
        columns = ('Process Name', 'Start Time', 'End Time', 'Duration', 'PID')
        self.history_tree = ui_kit.create_modern_treeview(history_frame, columns)
        
        # Configure columns
        self.history_tree.column('Process Name', width=200, anchor='w')
        self.history_tree.column('Start Time', width=150, anchor='center')
        self.history_tree.column('End Time', width=150, anchor='center')
        self.history_tree.column('Duration', width=120, anchor='center')
        self.history_tree.column('PID', width=80, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Load history
        self.load_history()
    
    def create_statistics_tab(self):
        """Create statistics tab"""
        stats_frame = ui_kit.create_modern_frame(self.notebook, 'Main.TFrame')
        self.notebook.add(stats_frame, text="📈 Statistics")
        
        # Statistics text widget with modern styling
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, width=80, 
                                                   font=('Segoe UI', 9),
                                                   bg='#FFFFFF', fg='#212529',
                                                   selectbackground='#2E86AB', selectforeground='#FFFFFF')
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Generate initial statistics
        self.generate_statistics()
    
    def create_log_tab(self):
        """Create log tab"""
        log_frame = ui_kit.create_modern_frame(self.notebook, 'Main.TFrame')
        self.notebook.add(log_frame, text="📝 Log")
        
        # Log text widget with modern styling
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80,
                                                  font=('Consolas', 9),
                                                  bg='#F8F9FA', fg='#212529',
                                                  selectbackground='#2E86AB', selectforeground='#FFFFFF')
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(15, 5))
        
        # Clear log button with modern styling
        clear_button = ui_kit.create_modern_button(log_frame, "🗑️ Clear Log", 
                                                  'Secondary.TButton', self.clear_log)
        clear_button.pack(pady=(0, 15))
        
        # Add initial log message
        self.add_log("Application started")
    
    def create_debug_tab(self):
        """Create debug tab for development"""
        debug_frame = ui_kit.create_modern_frame(self.notebook, 'Main.TFrame')
        self.notebook.add(debug_frame, text="🐛 Debug")
        
        # Debug controls frame
        controls_frame = ui_kit.create_modern_frame(debug_frame, 'Card.TFrame')
        controls_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # Debug buttons with modern styling
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(pady=10)
        
        ui_kit.create_modern_button(button_frame, "🗑️ Clear Debug Log", 
                                   'Danger.TButton', self.clear_debug_log).pack(side=tk.LEFT, padx=(0, 10))
        
        ui_kit.create_modern_button(button_frame, "🔄 Refresh Debug", 
                                   'Info.TButton', self.refresh_debug).pack(side=tk.LEFT, padx=(0, 10))
        
        ui_kit.create_modern_button(button_frame, "📊 System Info", 
                                   'Secondary.TButton', self.show_system_info).pack(side=tk.LEFT, padx=(0, 10))
        
        # Debug text widget with modern styling
        self.debug_text = scrolledtext.ScrolledText(debug_frame, height=20, width=80,
                                                    font=('Consolas', 9),
                                                    bg='#F8F9FA', fg='#212529',
                                                    selectbackground='#2E86AB', selectforeground='#FFFFFF')
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 15))
        
        # Load initial debug info
        self.refresh_debug()
    
    def get_current_processes(self):
        """Get list of currently running processes"""
        try:
            debug("Getting current processes")
            current_processes = {}
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    proc_info = proc.info
                    process_name = proc_info['name']
                    
                    if (process_name and 
                        not process_name.startswith('System') and
                        not process_name.startswith('Registry') and
                        proc_info['pid'] > 0):
                        
                        current_processes[process_name] = {
                            'pid': proc_info['pid'],
                            'create_time': proc_info['create_time'],
                            'first_seen': time.time()
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    debug(f"Access denied for process: {e}")
                    continue
            
            debug(f"Found {len(current_processes)} processes")
            return current_processes
            
        except Exception as e:
            error("Failed to get current processes", e)
            return {}
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        try:
            if self.monitoring:
                self.stop_monitoring()
            else:
                self.start_monitoring()
        except Exception as e:
            error("Failed to toggle monitoring", e)
            messagebox.showerror("Error", f"Failed to toggle monitoring: {e}")
    
    def start_monitoring(self):
        """Start monitoring"""
        try:
            info("Starting process monitoring")
            self.monitoring = True
            self.start_button.config(text="⏹️ Stop Monitoring", style='Danger.TButton')
            self.status_label.config(text="Status: Running", style='Success.TLabel')
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            self.monitor_thread.start()
            
            self.add_log("Monitoring started")
            info("Process monitoring started successfully")
            
        except Exception as e:
            error("Failed to start monitoring", e)
            self.monitoring = False
            self.start_button.config(text="🚀 Start Monitoring", style='Primary.TButton')
            self.status_label.config(text="Status: Error", style='Error.TLabel')
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            info("Stopping process monitoring")
            self.monitoring = False
            self.start_button.config(text="🚀 Start Monitoring", style='Primary.TButton')
            self.status_label.config(text="Status: Stopped", style='Status.TLabel')
            
            self.add_log("Monitoring stopped")
            self.save_log()
            info("Process monitoring stopped successfully")
            
        except Exception as e:
            error("Failed to stop monitoring", e)
            messagebox.showerror("Error", f"Failed to stop monitoring: {e}")
    
    def monitor_processes(self):
        """Monitor processes in background thread"""
        debug("Process monitoring thread started")
        while self.monitoring:
            try:
                current_processes = self.get_current_processes()
                
                # Check for new processes
                for process_name, proc_info in current_processes.items():
                    if process_name not in self.running_processes:
                        # New process started
                        self.running_processes[process_name] = {
                            'start_time': datetime.now(),
                            'pid': proc_info['pid'],
                            'create_time': proc_info['create_time']
                        }
                        
                        debug(f"New process detected: {process_name} (PID: {proc_info['pid']})")
                        
                        # Update GUI in main thread
                        self.root.after(0, lambda name=process_name, pid=proc_info['pid']: 
                                      self.add_log(f"New process started: {name} (PID: {pid})"))
                
                # Check for ended processes
                ended_processes = []
                for process_name in list(self.running_processes.keys()):
                    if process_name not in current_processes:
                        # Process ended
                        process_info = self.running_processes[process_name]
                        end_time = datetime.now()
                        duration = end_time - process_info['start_time']
                        
                        # Add to history
                        process_record = {
                            'process_name': process_name,
                            'start_time': process_info['start_time'].isoformat(),
                            'end_time': end_time.isoformat(),
                            'duration_seconds': int(duration.total_seconds()),
                            'duration_readable': str(duration).split('.')[0],
                            'pid': process_info['pid']
                        }
                        
                        self.process_history.append(process_record)
                        ended_processes.append(process_name)
                        
                        debug(f"Process ended: {process_name} (Duration: {process_record['duration_readable']})")
                        
                        # Update GUI in main thread
                        self.root.after(0, lambda name=process_name, dur=process_record['duration_readable']: 
                                      self.add_log(f"Process ended: {name} (Duration: {dur})"))
                
                # Remove ended processes
                for process_name in ended_processes:
                    del self.running_processes[process_name]
                
                # Update GUI
                self.root.after(0, self.refresh_processes)
                self.root.after(0, self.load_history)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                error("Error in monitoring thread", e)
                self.root.after(0, lambda: self.add_log(f"Monitoring error: {e}"))
                time.sleep(self.check_interval)
        
        debug("Process monitoring thread ended")
    
    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        if self.auto_refresh_enabled:
            self.auto_refresh_job = self.root.after(self.auto_refresh_interval, self.auto_refresh_callback)
            debug("Auto-refresh started")
    
    def stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        if self.auto_refresh_job:
            self.root.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
            debug("Auto-refresh stopped")
    
    def auto_refresh_callback(self):
        """Auto-refresh callback"""
        try:
            if self.auto_refresh_enabled:
                self.refresh_processes()
                self.load_history()
                self.generate_statistics()
                if DEVELOPMENT_MODE:
                    self.refresh_debug()
                
                # Schedule next refresh
                self.auto_refresh_job = self.root.after(self.auto_refresh_interval, self.auto_refresh_callback)
        except Exception as e:
            error("Auto-refresh error", e)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        try:
            self.auto_refresh_enabled = not self.auto_refresh_enabled
            
            if self.auto_refresh_enabled:
                self.auto_refresh_button.config(text="⏰ Auto Refresh: ON", style='Success.TButton')
                self.start_auto_refresh()
                self.add_log("Auto-refresh enabled")
            else:
                self.auto_refresh_button.config(text="⏰ Auto Refresh: OFF", style='Danger.TButton')
                self.stop_auto_refresh()
                self.add_log("Auto-refresh disabled")
                
        except Exception as e:
            error("Failed to toggle auto-refresh", e)
            messagebox.showerror("Error", f"Failed to toggle auto-refresh: {e}")
    
    def refresh_processes(self):
        """Refresh current processes display"""
        # Clear existing items
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)
        
        # Add current processes
        for process_name, info in self.running_processes.items():
            duration = datetime.now() - info['start_time']
            duration_str = str(duration).split('.')[0]
            
            self.process_tree.insert('', 'end', values=(
                process_name,
                info['pid'],
                info['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
                duration_str
            ))
    
    def load_history(self):
        """Load process history"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Add history items (show last 100)
        recent_history = self.process_history[-100:]
        for record in recent_history:
            self.history_tree.insert('', 'end', values=(
                record['process_name'],
                record['start_time'][:19],  # Remove microseconds
                record['end_time'][:19],
                record['duration_readable'],
                record['pid']
            ))
    
    def generate_statistics(self):
        """Generate and display statistics"""
        self.stats_text.delete(1.0, tk.END)
        
        if not self.process_history:
            self.stats_text.insert(tk.END, "No historical data available")
            return
        
        # Group by process name
        process_stats = {}
        total_duration = 0
        
        for record in self.process_history:
            name = record['process_name']
            duration = record['duration_seconds']
            
            if name not in process_stats:
                process_stats[name] = {
                    'count': 0,
                    'total_duration': 0,
                    'first_seen': record['start_time'],
                    'last_seen': record['end_time']
                }
            
            process_stats[name]['count'] += 1
            process_stats[name]['total_duration'] += duration
            process_stats[name]['last_seen'] = record['end_time']
            total_duration += duration
        
        # Sort by total duration
        sorted_processes = sorted(process_stats.items(), 
                                key=lambda x: x[1]['total_duration'], 
                                reverse=True)
        
        # Display statistics
        self.stats_text.insert(tk.END, "📊 Process Statistics\n")
        self.stats_text.insert(tk.END, "=" * 50 + "\n\n")
        
        self.stats_text.insert(tk.END, f"📝 Total Records: {len(self.process_history)}\n")
        self.stats_text.insert(tk.END, f"🔢 Different Applications: {len(process_stats)}\n")
        self.stats_text.insert(tk.END, f"⏱️ Total Monitoring Time: {total_duration // 3600:02d}:{(total_duration % 3600) // 60:02d}:00\n\n")
        
        self.stats_text.insert(tk.END, "📈 Most Used Applications (by total time):\n")
        self.stats_text.insert(tk.END, "-" * 40 + "\n")
        
        for i, (name, stats) in enumerate(sorted_processes[:15], 1):
            hours = stats['total_duration'] // 3600
            minutes = (stats['total_duration'] % 3600) // 60
            self.stats_text.insert(tk.END, f"{i:2d}. {name}\n")
            self.stats_text.insert(tk.END, f"    ⏱️ Total time: {hours:02d}:{minutes:02d}:00\n")
            self.stats_text.insert(tk.END, f"    🔄 Run count: {stats['count']}\n\n")
    
    def add_log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("Log cleared")
    
    def refresh_debug(self):
        """Refresh debug information"""
        try:
            self.debug_text.delete(1.0, tk.END)
            
            # System information
            self.debug_text.insert(tk.END, "🐛 Debug Information\n")
            self.debug_text.insert(tk.END, "=" * 50 + "\n\n")
            
            self.debug_text.insert(tk.END, f"Development Mode: {DEVELOPMENT_MODE}\n")
            self.debug_text.insert(tk.END, f"Debug Enabled: {DEBUG_ENABLED}\n")
            self.debug_text.insert(tk.END, f"Python Version: {sys.version}\n")
            self.debug_text.insert(tk.END, f"Tkinter Version: {tk.TkVersion}\n")
            self.debug_text.insert(tk.END, f"psutil Version: {psutil.__version__}\n\n")
            
            # Process monitoring status
            self.debug_text.insert(tk.END, "📊 Process Monitoring Status:\n")
            self.debug_text.insert(tk.END, f"Monitoring: {self.monitoring}\n")
            self.debug_text.insert(tk.END, f"Running Processes: {len(self.running_processes)}\n")
            self.debug_text.insert(tk.END, f"History Records: {len(self.process_history)}\n\n")
            
            # Debug log content
            if os.path.exists("debug.log"):
                self.debug_text.insert(tk.END, "📝 Debug Log (last 50 lines):\n")
                self.debug_text.insert(tk.END, "-" * 30 + "\n")
                
                try:
                    with open("debug.log", 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for line in lines[-50:]:  # Last 50 lines
                            self.debug_text.insert(tk.END, line)
                except Exception as e:
                    self.debug_text.insert(tk.END, f"Error reading debug log: {e}\n")
            else:
                self.debug_text.insert(tk.END, "📝 Debug log file not found\n")
                
        except Exception as e:
            error("Failed to refresh debug info", e)
            self.debug_text.insert(tk.END, f"Error refreshing debug info: {e}\n")
    
    def show_system_info(self):
        """Show detailed system information"""
        try:
            info_window = tk.Toplevel(self.root)
            info_window.title("System Information")
            info_window.geometry("600x400")
            
            text_widget = scrolledtext.ScrolledText(info_window, width=70, height=25)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # System info
            text_widget.insert(tk.END, "🖥️ System Information\n")
            text_widget.insert(tk.END, "=" * 50 + "\n\n")
            
            text_widget.insert(tk.END, f"OS: {os.name}\n")
            text_widget.insert(tk.END, f"Platform: {sys.platform}\n")
            text_widget.insert(tk.END, f"Python: {sys.version}\n")
            text_widget.insert(tk.END, f"Tkinter: {tk.TkVersion}\n")
            text_widget.insert(tk.END, f"psutil: {psutil.__version__}\n\n")
            
            # Memory info
            memory = psutil.virtual_memory()
            text_widget.insert(tk.END, f"Memory Total: {memory.total / (1024**3):.2f} GB\n")
            text_widget.insert(tk.END, f"Memory Available: {memory.available / (1024**3):.2f} GB\n")
            text_widget.insert(tk.END, f"Memory Used: {memory.percent}%\n\n")
            
            # CPU info
            cpu_count = psutil.cpu_count()
            text_widget.insert(tk.END, f"CPU Cores: {cpu_count}\n")
            text_widget.insert(tk.END, f"CPU Usage: {psutil.cpu_percent()}%\n\n")
            
            # Disk info
            disk = psutil.disk_usage('/')
            text_widget.insert(tk.END, f"Disk Total: {disk.total / (1024**3):.2f} GB\n")
            text_widget.insert(tk.END, f"Disk Used: {disk.used / (1024**3):.2f} GB\n")
            text_widget.insert(tk.END, f"Disk Free: {disk.free / (1024**3):.2f} GB\n")
            
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            error("Failed to show system info", e)
            messagebox.showerror("Error", f"Failed to show system info: {e}")
    
    def clear_debug_log(self):
        """Clear debug log"""
        try:
            clear_debug_log()
            self.refresh_debug()
            self.add_log("Debug log cleared")
        except Exception as e:
            error("Failed to clear debug log", e)
            messagebox.showerror("Error", f"Failed to clear debug log: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        try:
            info("Application closing...")
            if self.monitoring:
                self.stop_monitoring()
            self.stop_auto_refresh()
            self.save_log()
            info("Application closed successfully")
            self.root.destroy()
        except Exception as e:
            error("Error during application closing", e)
            self.root.destroy()

def main():
    try:
        info("Starting GUI application...")
        root = tk.Tk()
        app = ProcessMonitorGUI(root)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        info("GUI application started successfully")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        critical("Failed to start GUI application", e)
        messagebox.showerror("Critical Error", 
                           f"Failed to start application:\n{str(e)}\n\nCheck debug.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
