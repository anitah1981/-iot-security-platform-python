# Complete Build Script - Handles everything possible automatically
# For steps requiring user input, provides clear instructions

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Complete Mobile App Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = @()
$warnings = @()

# Step 1: Check EAS CLI
Write-Host "[1/6] Checking EAS CLI..." -ForegroundColor Yellow
$easCmd = Get-Command eas -ErrorAction SilentlyContinue
if ($easCmd) {
    $version = eas --version 2>&1
    Write-Host "  [OK] EAS CLI: $version" -ForegroundColor Green
} else {
    $errors += "EAS CLI not installed"
    Write-Host "  [ERROR] EAS CLI not found" -ForegroundColor Red
}
Write-Host ""

# Step 2: Check login
Write-Host "[2/6] Checking Expo login..." -ForegroundColor Yellow
if ($easCmd) {
    $loginCheck = eas whoami 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Logged in: $loginCheck" -ForegroundColor Green
        $isLoggedIn = $true
    } else {
        $warnings += "Not logged in - requires interactive login"
        Write-Host "  [ACTION REQUIRED] Not logged in" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Please run:" -ForegroundColor Cyan
        Write-Host "    eas login" -ForegroundColor White
        Write-Host ""
        Write-Host "  If you don't have an account:" -ForegroundColor Cyan
        Write-Host "    1. Go to: https://expo.dev" -ForegroundColor White
        Write-Host "    2. Sign up (free)" -ForegroundColor White
        Write-Host "    3. Run: eas login" -ForegroundColor White
        Write-Host ""
        $isLoggedIn = $false
    }
} else {
    $isLoggedIn = $false
}
Write-Host ""

# Step 3: Check configuration
Write-Host "[3/6] Checking project configuration..." -ForegroundColor Yellow
if (Test-Path "eas.json") {
    Write-Host "  [OK] eas.json exists" -ForegroundColor Green
} else {
    if ($isLoggedIn) {
        Write-Host "  Configuring project..." -ForegroundColor Yellow
        eas build:configure 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Project configured" -ForegroundColor Green
        } else {
            $warnings += "Could not auto-configure - run: eas build:configure"
        }
    } else {
        $warnings += "Cannot configure - login required first"
    }
}
Write-Host ""

# Step 4: Check API URL
Write-Host "[4/6] Checking API URL..." -ForegroundColor Yellow
$appJson = Get-Content "app.json" -Raw | ConvertFrom-Json
$apiUrl = $appJson.expo.extra.apiUrl

if ($apiUrl -eq "http://localhost:8000") {
    Write-Host "  [WARNING] API URL is localhost" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  For local testing, you need ngrok:" -ForegroundColor Cyan
    Write-Host "    1. Install: choco install ngrok (or download from ngrok.com)" -ForegroundColor White
    Write-Host "    2. Start: ngrok http 8000" -ForegroundColor White
    Write-Host "    3. Copy HTTPS URL and update app.json" -ForegroundColor White
    Write-Host ""
    Write-Host "  Or use your deployed backend URL" -ForegroundColor Cyan
    Write-Host ""
    $warnings += "API URL needs to be updated before building"
} else {
    Write-Host "  [OK] API URL: $apiUrl" -ForegroundColor Green
}
Write-Host ""

# Step 5: Check dependencies
Write-Host "[5/6] Checking dependencies..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    npm install 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
    } else {
        $errors += "Failed to install dependencies"
    }
}
Write-Host ""

# Step 6: Summary and next steps
Write-Host "[6/6] Build readiness check..." -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($errors.Count -eq 0 -and $warnings.Count -eq 0 -and $isLoggedIn) {
    Write-Host "[SUCCESS] Everything ready! Building apps..." -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Choose platform:" -ForegroundColor Cyan
    Write-Host "  1. iOS" -ForegroundColor White
    Write-Host "  2. Android" -ForegroundColor White
    Write-Host "  3. Both" -ForegroundColor White
    Write-Host ""
    $choice = Read-Host "Enter choice (1-3)"
    
    Write-Host ""
    Write-Host "Building... (this takes 10-15 minutes)" -ForegroundColor Yellow
    Write-Host ""
    
    if ($choice -eq "1") {
        eas build --platform ios --profile preview
    } elseif ($choice -eq "2") {
        eas build --platform android --profile preview
    } elseif ($choice -eq "3") {
        eas build --platform ios --profile preview
        Write-Host ""
        eas build --platform android --profile preview
    }
    
    Write-Host ""
    Write-Host "[SUCCESS] Build complete! Check output above for download links." -ForegroundColor Green
    
} else {
    if ($errors.Count -gt 0) {
        Write-Host "[ERRORS] Must fix:" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  - $error" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "[ACTIONS REQUIRED]:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Fix errors above" -ForegroundColor White
    Write-Host "  2. Complete actions above" -ForegroundColor White
    Write-Host "  3. Run this script again: .\complete-build.ps1" -ForegroundColor White
    Write-Host ""
    
    if (-not $isLoggedIn) {
        Write-Host "To login:" -ForegroundColor Cyan
        Write-Host "  eas login" -ForegroundColor White
        Write-Host ""
    }
    
    if ($apiUrl -eq "http://localhost:8000") {
        Write-Host "To update API URL:" -ForegroundColor Cyan
        Write-Host "  Edit app.json and change 'apiUrl' to your backend URL" -ForegroundColor White
        Write-Host ""
    }
}

Write-Host "========================================" -ForegroundColor Cyan
if ([Environment]::UserInteractive) {
    Read-Host "Press Enter to exit"
}
