# PowerShell script to configure Windows Firewall for Expo
# Must be run as Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuring Windows Firewall for Expo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[1/3] Allowing Node.js through firewall..." -ForegroundColor Yellow

# Find Node.js executable
$nodePaths = @(
    "C:\Program Files\nodejs\node.exe",
    "C:\Program Files (x86)\nodejs\node.exe",
    "$env:ProgramFiles\nodejs\node.exe",
    "$env:ProgramFiles(x86)\nodejs\node.exe"
)

$nodePath = $null
foreach ($path in $nodePaths) {
    if (Test-Path $path) {
        $nodePath = $path
        break
    }
}

if ($nodePath) {
    Write-Host "Found Node.js at: $nodePath" -ForegroundColor Green
    
    # Add firewall rule for Node.js
    $ruleName = "Node.js JavaScript Runtime"
    $existingRule = Get-NetFirewallApplicationFilter -Program $nodePath -ErrorAction SilentlyContinue
    
    if (-not $existingRule) {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Program $nodePath -Action Allow -Profile Private,Public | Out-Null
        Write-Host "Added Node.js to firewall rules" -ForegroundColor Green
    } else {
        Write-Host "Node.js already in firewall rules" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: Could not find Node.js. Please add it manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/3] Allowing port 8081 through firewall..." -ForegroundColor Yellow

# Check if port 8081 rule exists
$portRule = Get-NetFirewallPortFilter -LocalPort 8081 -ErrorAction SilentlyContinue

if (-not $portRule) {
    New-NetFirewallRule -DisplayName "Expo Dev Server" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow -Profile Domain,Private,Public | Out-Null
    Write-Host "Added port 8081 to firewall rules" -ForegroundColor Green
} else {
    Write-Host "Port 8081 already allowed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/3] Enabling network discovery..." -ForegroundColor Yellow

# Enable network discovery (requires registry edit)
try {
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\FDResPub"
    if (Test-Path $regPath) {
        Set-ItemProperty -Path $regPath -Name "Start" -Value 2 -ErrorAction SilentlyContinue
        Write-Host "Network discovery enabled" -ForegroundColor Green
    }
} catch {
    Write-Host "Could not modify network discovery (may require manual setup)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Firewall configuration complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart Expo: npm run start:lan" -ForegroundColor White
Write-Host "2. Wait 60 seconds" -ForegroundColor White
Write-Host "3. In Expo Go, pull down to refresh" -ForegroundColor White
Write-Host "4. Your server should appear!" -ForegroundColor White
Write-Host ""
pause
