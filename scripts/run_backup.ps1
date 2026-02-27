$ErrorActionPreference = "Stop"
Set-Location "c:\IoT-security-app-python"
$env:PYTHONPATH = "c:\IoT-security-app-python"
& python scripts/backup_manual.py
