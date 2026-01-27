# Complete Setup and Build Script
# Handles login, configuration, and building

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Mobile App Setup & Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check EAS CLI
Write-Host "[1/6] Checking EAS CLI..." -ForegroundColor Yellow
$easCmd = Get-Command eas -ErrorAction SilentlyContinue
if (-not $easCmd) {
    Write-Host "Installing EAS CLI..." -ForegroundColor Yellow
    npm install -g eas-cli
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install EAS CLI" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host "[OK] EAS CLI ready" -ForegroundColor Green
Write-Host ""

# Step 2: Check login
Write-Host "[2/6] Checking Expo login..." -ForegroundColor Yellow
$loginCheck = eas whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Please login:" -ForegroundColor Yellow
    Write-Host "1. Create free account at https://expo.dev" -ForegroundColor Cyan
    Write-Host "2. Then run: eas login" -ForegroundColor Cyan
    Write-Host ""
    $login = Read-Host "Have you created an Expo account? (y/n)"
    if ($login -eq "y" -or $login -eq "Y") {
        eas login
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Login failed" -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "Please create an account at https://expo.dev first" -ForegroundColor Yellow
        Write-Host "Then run this script again" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[OK] Logged in as: $loginCheck" -ForegroundColor Green
}
Write-Host ""

# Step 3: Configure project
Write-Host "[3/6] Configuring project..." -ForegroundColor Yellow
if (-not (Test-Path "eas.json")) {
    Write-Host "Running eas build:configure..." -ForegroundColor Yellow
    eas build:configure
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Configuration failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[OK] Project already configured" -ForegroundColor Green
}
Write-Host ""

# Step 4: Check API URL
Write-Host "[4/6] Checking API URL..." -ForegroundColor Yellow
$appJson = Get-Content "app.json" -Raw | ConvertFrom-Json
$apiUrl = $appJson.expo.extra.apiUrl

if ($apiUrl -eq "http://localhost:8000") {
    Write-Host "[WARNING] API URL is still localhost" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "1. Use ngrok (for local testing)" -ForegroundColor White
    Write-Host "2. Enter deployed backend URL" -ForegroundColor White
    Write-Host "3. Use placeholder (update later)" -ForegroundColor White
    Write-Host ""
    $choice = Read-Host "Choose option (1-3)"
    
    if ($choice -eq "1") {
        # Check if ngrok is installed
        $ngrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
        if (-not $ngrokCmd) {
            Write-Host "ngrok not found. Installing..." -ForegroundColor Yellow
            choco install ngrok -y
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[WARNING] Could not install ngrok. Using placeholder URL." -ForegroundColor Yellow
                $newUrl = "https://your-backend-url.com"
            } else {
                Write-Host "Starting ngrok tunnel..." -ForegroundColor Yellow
                Write-Host "Please start ngrok in another terminal: ngrok http 8000" -ForegroundColor Cyan
                Write-Host "Then enter the HTTPS URL below:" -ForegroundColor Cyan
                $newUrl = Read-Host "Enter ngrok HTTPS URL"
            }
        } else {
            Write-Host "Please start ngrok in another terminal: ngrok http 8000" -ForegroundColor Cyan
            $newUrl = Read-Host "Enter ngrok HTTPS URL"
        }
    } elseif ($choice -eq "2") {
        $newUrl = Read-Host "Enter your backend URL (e.g., https://your-app.railway.app)"
    } else {
        $newUrl = "https://your-backend-url.com"
        Write-Host "Using placeholder URL. Update app.json before building!" -ForegroundColor Yellow
    }
    
    # Update app.json
    $appJson.expo.extra.apiUrl = $newUrl
    $appJson | ConvertTo-Json -Depth 10 | Set-Content "app.json"
    Write-Host "[OK] API URL updated to: $newUrl" -ForegroundColor Green
} else {
    Write-Host "[OK] API URL configured: $apiUrl" -ForegroundColor Green
}
Write-Host ""

# Step 5: Pre-build validation
Write-Host "[5/6] Running pre-build checks..." -ForegroundColor Yellow
& "$PSScriptRoot\pre-build-check.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Pre-build checks failed. Please fix issues above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 6: Build
Write-Host "[6/6] Ready to build!" -ForegroundColor Yellow
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
    Write-Host "This will take 10-15 minutes..." -ForegroundColor Yellow
    eas build --platform ios --profile preview
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "Building Android app..." -ForegroundColor Cyan
    Write-Host "This will take 10-15 minutes..." -ForegroundColor Yellow
    eas build --platform android --profile preview
} elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "Building iOS app..." -ForegroundColor Cyan
    Write-Host "This will take 10-15 minutes..." -ForegroundColor Yellow
    eas build --platform ios --profile preview
    Write-Host ""
    Write-Host "Building Android app..." -ForegroundColor Cyan
    Write-Host "This will take 10-15 minutes..." -ForegroundColor Yellow
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
