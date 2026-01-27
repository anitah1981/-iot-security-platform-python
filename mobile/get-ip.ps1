# PowerShell script to get IP and start Expo for iPhone

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Expo for iPhone (LAN Mode)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get IP address
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress

if ($ipAddress) {
    Write-Host "Your IP address: $ipAddress" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "IN EXPO GO APP:" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "1. Open Expo Go on your iPhone" -ForegroundColor White
    Write-Host "2. Tap 'Enter URL manually'" -ForegroundColor White
    Write-Host "3. Type: exp://$ipAddress:8081" -ForegroundColor Green
    Write-Host "4. Tap 'Connect'" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Starting Expo..." -ForegroundColor Yellow
    Write-Host ""
    
    # Start Expo
    npm run start:lan
} else {
    Write-Host "Could not find IP address. Please check your network connection." -ForegroundColor Red
    Write-Host ""
    Write-Host "Starting Expo anyway..." -ForegroundColor Yellow
    npm run start:lan
}
