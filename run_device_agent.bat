@echo off
REM Run the device agent (heartbeats + watchdog). Use this from the project root or double-click.
cd /d "%~dp0"
python agent\device_agent.py
pause
