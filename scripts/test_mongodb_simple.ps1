# PowerShell script to test MongoDB connection
# Usage: .\scripts\test_mongodb_simple.ps1

Write-Host ""
Write-Host "MongoDB Atlas Connection Test" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Prompt for connection string
$mongoUri = Read-Host "Paste your MongoDB connection string (with password and /iot_security at the end)"

if ([string]::IsNullOrWhiteSpace($mongoUri)) {
    Write-Host "No connection string provided. Exiting." -ForegroundColor Red
    exit 1
}

# Set environment variable and run test
$env:MONGO_URI = $mongoUri
python scripts\test_mongodb_connection.py

# Clear the env var
Remove-Item Env:\MONGO_URI
