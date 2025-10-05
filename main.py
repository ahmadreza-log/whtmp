import psutil
import json
import time
import threading
from datetime import datetime
import os

class ProcessMonitor:
    def __init__(self, log_file="process_log.json"):
        self.log_file = log_file
        self.running_processes = {}  # Dictionary to store process info
        self.process_history = []    # List to store completed processes
        self.monitoring = False
        self.check_interval = 2  # Check every 2 seconds
        
        # Load existing log if it exists
        self.load_existing_log()
    
    def load_existing_log(self):
        """Load existing process history from log file"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.process_history = data.get('process_history', [])
                    print(f"✅ Loaded {len(self.process_history)} existing records")
            except Exception as e:
                print(f"⚠️ Error loading existing log: {e}")
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
            print(f"💾 Log saved to {self.log_file}")
        except Exception as e:
            print(f"❌ Error saving log: {e}")
    
    def get_current_processes(self):
        """Get list of currently running processes"""
        current_processes = {}
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            try:
                proc_info = proc.info
                process_name = proc_info['name']
                
                # Skip system processes and duplicates
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
    
    def start_monitoring(self):
        """Start the monitoring process"""
        self.monitoring = True
        print("🚀 Starting process monitoring...")
        print("💡 Press Ctrl+C to stop monitoring")
        
        try:
            while self.monitoring:
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
                        print(f"🟢 New process started: {process_name} (PID: {proc_info['pid']})")
                
                # Check for ended processes
                ended_processes = []
                for process_name in list(self.running_processes.keys()):
                    if process_name not in current_processes:
                        # Process ended
                        process_info = self.running_processes[process_name]
                        end_time = datetime.now()
                        
                        # Calculate duration
                        duration = end_time - process_info['start_time']
                        
                        # Add to history
                        process_record = {
                            'process_name': process_name,
                            'start_time': process_info['start_time'].isoformat(),
                            'end_time': end_time.isoformat(),
                            'duration_seconds': int(duration.total_seconds()),
                            'duration_readable': str(duration).split('.')[0],  # Remove microseconds
                            'pid': process_info['pid']
                        }
                        
                        self.process_history.append(process_record)
                        ended_processes.append(process_name)
                        
                        print(f"🔴 Process ended: {process_name} (Duration: {process_record['duration_readable']})")
                
                # Remove ended processes from running list
                for process_name in ended_processes:
                    del self.running_processes[process_name]
                
                # Save log every 10 checks (20 seconds)
                if len(self.process_history) % 10 == 0 and len(self.process_history) > 0:
                    self.save_log()
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped...")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring and save final log"""
        self.monitoring = False
        
        # Save final log
        self.save_log()
        
        # Print summary
        print(f"\n📊 Summary Report:")
        print(f"📁 Log file: {self.log_file}")
        print(f"📝 Total records saved: {len(self.process_history)}")
        
        if self.process_history:
            print(f"⏰ Last activity: {self.process_history[-1]['process_name']}")
            print(f"🕐 Last record time: {self.process_history[-1]['end_time']}")
    
    def show_current_status(self):
        """Show currently running processes"""
        if not self.running_processes:
            print("🔍 No processes currently running")
            return
        
        print(f"\n📋 Currently Running Processes ({len(self.running_processes)} processes):")
        print("-" * 60)
        for process_name, info in self.running_processes.items():
            duration = datetime.now() - info['start_time']
            print(f"🟢 {process_name}")
            print(f"   📅 Started: {info['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ⏱️ Running for: {str(duration).split('.')[0]}")
            print(f"   🔢 PID: {info['pid']}")
            print()
    
    def show_statistics(self):
        """Show statistics from log file"""
        if not self.process_history:
            print("📊 No historical statistics available")
            return
        
        print(f"\n📊 Overall Statistics:")
        print("-" * 40)
        
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
        
        print(f"📈 Most Used Applications (by total time):")
        for i, (name, stats) in enumerate(sorted_processes[:10], 1):
            hours = stats['total_duration'] // 3600
            minutes = (stats['total_duration'] % 3600) // 60
            print(f"{i:2d}. {name}")
            print(f"    ⏱️ Total time: {hours:02d}:{minutes:02d}:00")
            print(f"    🔄 Run count: {stats['count']}")
            print()
        
        print(f"📊 Overall Stats:")
        print(f"   📝 Total records: {len(self.process_history)}")
        print(f"   🔢 Different applications: {len(process_stats)}")
        print(f"   ⏱️ Total monitoring time: {total_duration // 3600:02d}:{(total_duration % 3600) // 60:02d}:00")

def main():
    print("🖥️ Windows Process Monitor")
    print("=" * 50)
    
    monitor = ProcessMonitor()
    
    while True:
        print("\n📋 Main Menu:")
        print("1. 🚀 Start Monitoring")
        print("2. 📊 Show Current Status")
        print("3. 📈 Show Historical Statistics")
        print("4. 🛑 Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            monitor.start_monitoring()
        elif choice == '2':
            monitor.show_current_status()
        elif choice == '3':
            monitor.show_statistics()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice! Please enter a number between 1-4.")

if __name__ == "__main__":
    main()