@echo off
title Kishor Farm Merger Pro - Flet GUI
cd /d "%~dp0"
echo.
echo ========================================
echo   Farm Merger Pro - Flet GUI Edition
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from: https://python.org/downloads/
    pause
    exit /b 1
)

REM Check if Flet is installed
python -c "import flet" >nul 2>&1
if errorlevel 1 (
    echo [1/2] Installing Flet...
    pip install flet>=0.24.0
    if errorlevel 1 (
        echo ERROR: Failed to install Flet
        echo Please run manually: pip install flet
        pause
        exit /b 1
    )
    echo Flet installed successfully
)

echo [2/2] Starting Flet GUI...
echo.
echo Glassmorphism Edition with smooth animations
echo.

REM Change to the directory where the script is located
cd /d "%~dp0"

REM Run the Flet GUI
python gui_flet.py

if errorlevel 1 (
    echo.
    echo Error occurred. Check the error message above.
    pause
) else (
    echo.
    echo Application closed successfully.
)

