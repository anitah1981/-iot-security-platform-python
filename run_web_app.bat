@echo off
REM Run the Pro-Alert web app. Use this from the project root or double-click.
cd /d "%~dp0"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
