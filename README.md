# 🖥️ Windows Process Monitor

This application is designed to track and monitor running applications on Windows systems.

## ✨ Features

- 🔍 **Automatic Process Detection**: Tracks all running applications
- ⏰ **Time Range Tracking**: Records start and end times for each application
- 💾 **Smart Storage**: Information is saved to a JSON file
- 📊 **Statistics**: Shows comprehensive usage statistics for applications
- 🚫 **No Spam**: Each application is recorded only once per session

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- Windows 10/11

### Installation Steps

1. **Clone the project:**
```bash
git clone <repository-url>
cd whtmp
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
# Modern GUI version
python main.py

# Or use the launcher
run.bat
```

## 📖 Usage

### Modern GUI Application
After running `python main.py` or `run.bat`, a modern, beautiful interface will open with:

- **📋 Current Processes Tab**: Shows currently running applications with modern cards
- **📊 Process History Tab**: Displays historical process data with visual indicators
- **📈 Statistics Tab**: Shows usage statistics and analytics
- **📝 Log Tab**: Real-time monitoring log with modern styling
- **🐛 Debug Tab**: Development debug information (development mode only)

#### Modern GUI Features:
- **🚀 Start/Stop Monitoring**: Beautiful toggle button with color changes
- **⏰ Auto Refresh**: Smart switch with real-time updates
- **💾 Save Log**: Modern save button with success feedback
- **📊 Status Indicator**: Color-coded status with emojis
- **🎨 Modern Design**: Material Design inspired UI
- **📱 Responsive**: Adapts to different window sizes
- **⚡ Real-time**: Smooth animations and updates

## 📁 Output Files

### `process_log.json`
This file contains all monitoring information:

```json
{
  "last_updated": "2024-01-15T10:30:45.123456",
  "process_history": [
    {
      "process_name": "chrome.exe",
      "start_time": "2024-01-15T09:00:00.000000",
      "end_time": "2024-01-15T09:30:00.000000", 
      "duration_seconds": 1800,
      "duration_readable": "0:30:00",
      "pid": 1234
    }
  ]
}
```

## 🔧 Configuration

You can modify the following settings in the code:

- `check_interval`: Time interval for checking processes (default: 2 seconds)
- `log_file`: Log file name (default: process_log.json)

## 📊 Example Output

```
🖥️ Windows Process Monitor
==================================================

📋 Main Menu:
1. 🚀 Start Monitoring
2. 📊 Show Current Status
3. 📈 Show Historical Statistics  
4. 🛑 Exit

Select option (1-4): 1

🚀 Starting process monitoring...
💡 Press Ctrl+C to stop monitoring

🟢 New process started: chrome.exe (PID: 1234)
🟢 New process started: notepad.exe (PID: 5678)
🔴 Process ended: notepad.exe (Duration: 0:05:23)
```

## ⚠️ Important Notes

- Use `Ctrl+C` to stop monitoring
- The application requires system access permissions
- Log file is automatically saved every 20 seconds
- Previous data is loaded if it exists

## 🛠️ Troubleshooting

### Access Error
If you encounter access errors, run the application as Administrator.

### psutil Error
If you have issues with psutil:
```bash
pip install --upgrade psutil
```

## 📝 License

This project is released under the MIT license.