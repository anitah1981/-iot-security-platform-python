# Auto-Build Script - Handles everything automatically
# This script will guide you through the build process

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Auto-Build Mobile Apps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check login
Write-Host "Checking Expo login..." -ForegroundColor Yellow
$loginCheck = eas whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  You need to login to Expo first!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Cyan
    Write-Host "  eas login" -ForegroundColor White
    Write-Host ""
    Write-Host "If you don't have an account:" -ForegroundColor Cyan
    Write-Host "  1. Go to: https://expo.dev" -ForegroundColor White
    Write-Host "  2. Sign up (free)" -ForegroundColor White
    Write-Host "  3. Then run: eas login" -ForegroundColor White
    Write-Host ""
    $proceed = Read-Host "Have you logged in? (y/n)"
    if ($proceed -ne "y" -and $proceed -ne "Y") {
        Write-Host "Please login first, then run this script again." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✓ Logged in as: $loginCheck" -ForegroundColor Green
}
Write-Host ""

# Check API URL
Write-Host "Checking API URL configuration..." -ForegroundColor Yellow
$appJson = Get-Content "app.json" -Raw | ConvertFrom-Json
$apiUrl = $appJson.expo.extra.apiUrl

if ($apiUrl -eq "http://localhost:8000") {
    Write-Host "⚠️  API URL is still localhost" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  1. Use ngrok (for local testing)" -ForegroundColor White
    Write-Host "  2. Enter deployed backend URL" -ForegroundColor White
    Write-Host "  3. Skip for now (update manually later)" -ForegroundColor White
    Write-Host ""
    $choice = Read-Host "Choose option (1-3)"
    
    if ($choice -eq "1") {
        # Check if ngrok is installed
        $ngrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
        if (-not $ngrokCmd) {
            Write-Host ""
            Write-Host "ngrok not found. Installing..." -ForegroundColor Yellow
            choco install ngrok -y 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Could not install ngrok automatically." -ForegroundColor Red
                Write-Host "Please install manually: choco install ngrok" -ForegroundColor Yellow
                Write-Host "Or download from: https://ngrok.com/download" -ForegroundColor Yellow
                $choice = "3"
            }
        }
        
        if ($choice -eq "1") {
            Write-Host ""
            Write-Host "To use ngrok:" -ForegroundColor Cyan
            Write-Host "  1. Make sure your backend is running on port 8000" -ForegroundColor White
            Write-Host "  2. Open another terminal and run: ngrok http 8000" -ForegroundColor White
            Write-Host "  3. Copy the HTTPS URL (example: https://abc123.ngrok.io)" -ForegroundColor White
            Write-Host ""
            $ngrokUrl = Read-Host "Enter ngrok HTTPS URL"
            if ($ngrokUrl) {
                $appJson.expo.extra.apiUrl = $ngrokUrl
                $appJson | ConvertTo-Json -Depth 10 | Set-Content "app.json"
                Write-Host "✓ API URL updated to: $ngrokUrl" -ForegroundColor Green
            }
        }
    } elseif ($choice -eq "2") {
        Write-Host ""
        $backendUrl = Read-Host "Enter your backend URL (e.g., https://your-app.railway.app)"
        if ($backendUrl) {
            $appJson.expo.extra.apiUrl = $backendUrl
            $appJson | ConvertTo-Json -Depth 10 | Set-Content "app.json"
            Write-Host "✓ API URL updated to: $backendUrl" -ForegroundColor Green
        }
    } else {
        Write-Host ""
        Write-Host "⚠️  Remember to update API URL in app.json before building!" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ API URL configured: $apiUrl" -ForegroundColor Green
}
Write-Host ""

# Run pre-build check
Write-Host "Running pre-build validation..." -ForegroundColor Yellow
& "$PSScriptRoot\pre-build-check.ps1" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "⚠️  Pre-build checks found issues. Please review above." -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}
Write-Host ""

# Build
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ready to Build!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Choose platform:" -ForegroundColor Cyan
Write-Host "  1. iOS (iPhone)" -ForegroundColor White
Write-Host "  2. Android" -ForegroundColor White
Write-Host "  3. Both" -ForegroundColor White
Write-Host ""
$platform = Read-Host "Enter choice (1-3)"

Write-Host ""
Write-Host "⏱️  Building will take 10-15 minutes..." -ForegroundColor Yellow
Write-Host ""

if ($platform -eq "1") {
    Write-Host "Building iOS app..." -ForegroundColor Cyan
    eas build --platform ios --profile preview
} elseif ($platform -eq "2") {
    Write-Host "Building Android app..." -ForegroundColor Cyan
    eas build --platform android --profile preview
} elseif ($platform -eq "3") {
    Write-Host "Building iOS app..." -ForegroundColor Cyan
    eas build --platform ios --profile preview
    Write-Host ""
    Write-Host "Building Android app..." -ForegroundColor Cyan
    eas build --platform android --profile preview
} else {
    Write-Host "Invalid choice!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check the output above for download links." -ForegroundColor Yellow
Write-Host ""
