import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import json
import time
import threading
from datetime import datetime
import os

class ProcessMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Process Monitor")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Process monitoring variables
        self.running_processes = {}
        self.process_history = []
        self.monitoring = False
        self.check_interval = 2
        self.log_file = "process_log.json"
        
        # Load existing log
        self.load_existing_log()
        
        # Create GUI
        self.create_widgets()
        
        # Start monitoring thread
        self.monitor_thread = None
        
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
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🖥️ Windows Process Monitor", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, text="🚀 Start Monitoring", 
                                      command=self.toggle_monitoring, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh button
        refresh_button = ttk.Button(control_frame, text="🔄 Refresh", 
                                   command=self.refresh_processes)
        refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Save button
        save_button = ttk.Button(control_frame, text="💾 Save Log", 
                                command=self.save_log)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Status: Stopped", 
                                     foreground='red')
        self.status_label.pack(side=tk.RIGHT)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Current Processes Tab
        self.create_current_processes_tab()
        
        # Process History Tab
        self.create_history_tab()
        
        # Statistics Tab
        self.create_statistics_tab()
        
        # Log Tab
        self.create_log_tab()
        
        # Initial refresh
        self.refresh_processes()
    
    def create_current_processes_tab(self):
        """Create current processes tab"""
        current_frame = ttk.Frame(self.notebook)
        self.notebook.add(current_frame, text="📋 Current Processes")
        
        # Treeview for processes
        columns = ('Process Name', 'PID', 'Start Time', 'Duration')
        self.process_tree = ttk.Treeview(current_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(current_frame, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_history_tab(self):
        """Create process history tab"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📊 Process History")
        
        # Treeview for history
        columns = ('Process Name', 'Start Time', 'End Time', 'Duration', 'PID')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load history
        self.load_history()
    
    def create_statistics_tab(self):
        """Create statistics tab"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📈 Statistics")
        
        # Statistics text widget
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, width=80)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generate initial statistics
        self.generate_statistics()
    
    def create_log_tab(self):
        """Create log tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="📝 Log")
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clear log button
        clear_button = ttk.Button(log_frame, text="🗑️ Clear Log", 
                                 command=self.clear_log)
        clear_button.pack(pady=(0, 10))
        
        # Add initial log message
        self.add_log("Application started")
    
    def get_current_processes(self):
        """Get list of currently running processes"""
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
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return current_processes
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self.monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start monitoring"""
        self.monitoring = True
        self.start_button.config(text="⏹️ Stop Monitoring")
        self.status_label.config(text="Status: Running", foreground='green')
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.monitor_thread.start()
        
        self.add_log("Monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.start_button.config(text="🚀 Start Monitoring")
        self.status_label.config(text="Status: Stopped", foreground='red')
        
        self.add_log("Monitoring stopped")
        self.save_log()
    
    def monitor_processes(self):
        """Monitor processes in background thread"""
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
                self.root.after(0, lambda: self.add_log(f"Error: {e}"))
                time.sleep(self.check_interval)
    
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
    
    def on_closing(self):
        """Handle window closing"""
        if self.monitoring:
            self.stop_monitoring()
        self.save_log()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ProcessMonitorGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
