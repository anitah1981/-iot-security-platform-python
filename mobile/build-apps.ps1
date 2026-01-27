# IoT Security Mobile App Builder (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IoT Security Mobile App Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

# Step 1: Check EAS CLI
Write-Host "[1/4] Checking EAS CLI installation..." -ForegroundColor Yellow
try {
    $null = Get-Command eas -ErrorAction Stop
    Write-Host "EAS CLI found!" -ForegroundColor Green
} catch {
    Write-Host "EAS CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g eas-cli
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install EAS CLI" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host ""

# Step 2: Check login
Write-Host "[2/4] Checking login status..." -ForegroundColor Yellow
$loginCheck = eas whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Please login:" -ForegroundColor Yellow
    eas login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Login failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Already logged in!" -ForegroundColor Green
}
Write-Host ""

# Step 3: Check configuration
Write-Host "[3/4] Checking project configuration..." -ForegroundColor Yellow
if (-not (Test-Path "eas.json")) {
    Write-Host "Configuring project..." -ForegroundColor Yellow
    eas build:configure
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Configuration failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "Project already configured!" -ForegroundColor Green
}
Write-Host ""

# Step 4: Pre-build validation
Write-Host "[4/5] Running pre-build checks..." -ForegroundColor Yellow
& "$PSScriptRoot\pre-build-check.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Pre-build checks failed. Please fix issues above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 5: Build
Write-Host "[5/5] Ready to build!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Choose platform:" -ForegroundColor Cyan
Write-Host "  1. iOS (iPhone)"
Write-Host "  2. Android"
Write-Host "  3. Both"
Write-Host ""
$choice = Read-Host "Enter choice (1-3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "Building iOS app..." -ForegroundColor Cyan
    eas build --platform ios --profile preview
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Building Android app..." -ForegroundColor Cyan
    eas build --platform android --profile preview
} elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "Building iOS app..." -ForegroundColor Cyan
    eas build --platform ios --profile preview
    Write-Host ""
    Write-Host "Building Android app..." -ForegroundColor Cyan
    eas build --platform android --profile preview
} else {
    Write-Host "Invalid choice!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the output above for download links." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
