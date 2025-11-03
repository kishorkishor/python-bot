@echo off
title Kishor Farm Merger Pro - Production Launcher
color 0A
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║             Kishor Farm Merger Pro v2.2             ║
echo  ║              Production-Ready Auto Merger                   ║
echo  ║                    Made by Kishor                           ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7+ from: https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

REM Check Python version
echo [2/4] Checking Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detected

REM Check if required files exist
echo [3/4] Checking required files...
if not exist "gui.py" (
    echo ❌ ERROR: gui.py not found
    echo Please make sure all files are in the same folder
    pause
    exit /b 1
)
if not exist "item_finder.py" (
    echo ❌ ERROR: item_finder.py not found
    pause
    exit /b 1
)
if not exist "merging_points_selector.py" (
    echo ❌ ERROR: merging_points_selector.py not found
    pause
    exit /b 1
)
if not exist "screen_area_selector.py" (
    echo ❌ ERROR: screen_area_selector.py not found
    pause
    exit /b 1
)
if not exist "img" (
    echo ❌ ERROR: img folder not found
    pause
    exit /b 1
)
echo ✅ All required files found

REM Check dependencies
echo [4/4] Checking dependencies...
python -c "import dearpygui, keyboard, pyautogui, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing required packages...
    pip install dearpygui keyboard pyautogui opencv-python numpy
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        echo Please run: pip install dearpygui keyboard pyautogui opencv-python numpy
        pause
        exit /b 1
    )
)
echo ✅ Dependencies ready

REM Launch application
echo.
echo 🚀 Launching Kishor Farm Merger Pro...
echo.
echo 💡 TIP: Press = key to instantly start/stop merging
echo 💡 TIP: System works with any box count (even 0!)
echo.

python gui.py

REM Handle exit
if errorlevel 1 (
    echo.
    echo ❌ Application closed with an error (Code: %errorlevel%)
    echo.
    echo Common fixes:
    echo - Make sure all image files are in the img/ folder
    echo - Check that your screen area selection is correct
    echo - Verify box button position is accurate
    echo.
    pause
) else (
    echo.
    echo ✅ Application closed successfully
)
