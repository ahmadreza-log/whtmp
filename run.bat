@echo off
echo Windows Process Monitor
echo ======================
echo.

echo Checking dependencies...
python -c "import flet, psutil" 2>nul
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install packages!
        pause
        exit /b 1
    )
    echo Packages installed successfully!
) else (
    echo All packages are already installed.
)

echo.
echo Starting application...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Application failed to start!
    pause
)
