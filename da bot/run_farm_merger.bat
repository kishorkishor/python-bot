@echo off
title Kishor Farm Merger - Quick Launch
cd /d "%~dp0"
echo Starting Kishor Farm Merger...
python gui.py
if errorlevel 1 (
    echo Error occurred. Press any key to exit.
    pause >nul
)



