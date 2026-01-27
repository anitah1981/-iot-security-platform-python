# Pre-Build Validation Script
# Checks everything before building mobile apps

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pre-Build Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = @()
$warnings = @()

# Check 1: EAS CLI
Write-Host "[1/7] Checking EAS CLI..." -ForegroundColor Yellow
try {
    $null = Get-Command eas -ErrorAction Stop
    $version = eas --version 2>&1
    Write-Host "  ✓ EAS CLI installed: $version" -ForegroundColor Green
} catch {
    $errors += "EAS CLI not installed. Run: npm install -g eas-cli"
    Write-Host "  ✗ EAS CLI not found" -ForegroundColor Red
}
Write-Host ""

# Check 2: Login status
Write-Host "[2/7] Checking Expo login..." -ForegroundColor Yellow
$loginCheck = eas whoami 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Logged in as: $loginCheck" -ForegroundColor Green
} else {
    $warnings += "Not logged in. Run: eas login"
    Write-Host "  ⚠ Not logged in" -ForegroundColor Yellow
}
Write-Host ""

# Check 3: Project configuration
Write-Host "[3/7] Checking project configuration..." -ForegroundColor Yellow
if (Test-Path "eas.json") {
    Write-Host "  ✓ eas.json exists" -ForegroundColor Green
} else {
    $warnings += "eas.json not found. Run: eas build:configure"
    Write-Host "  ⚠ eas.json not found" -ForegroundColor Yellow
}
Write-Host ""

# Check 4: app.json exists
Write-Host "[4/7] Checking app.json..." -ForegroundColor Yellow
if (Test-Path "app.json") {
    Write-Host "  ✓ app.json exists" -ForegroundColor Green
    
    # Check API URL
    $appJson = Get-Content "app.json" -Raw | ConvertFrom-Json
    $apiUrl = $appJson.expo.extra.apiUrl
    if ($apiUrl -eq "http://localhost:8000") {
        $warnings += "API URL is still localhost. Update in app.json before building."
        Write-Host "  ⚠ API URL is localhost: $apiUrl" -ForegroundColor Yellow
    } else {
        Write-Host "  ✓ API URL configured: $apiUrl" -ForegroundColor Green
    }
} else {
    $errors += "app.json not found!"
    Write-Host "  ✗ app.json not found" -ForegroundColor Red
}
Write-Host ""

# Check 5: Node modules
Write-Host "[5/7] Checking dependencies..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "  ✓ node_modules exists" -ForegroundColor Green
} else {
    $warnings += "node_modules not found. Run: npm install"
    Write-Host "  ⚠ node_modules not found" -ForegroundColor Yellow
}
Write-Host ""

# Check 6: Required files
Write-Host "[6/7] Checking required files..." -ForegroundColor Yellow
$requiredFiles = @("App.js", "package.json", "babel.config.js")
$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        $errors += "Required file missing: $file"
        Write-Host "  ✗ $file missing" -ForegroundColor Red
        $allFilesExist = $false
    }
}
Write-Host ""

# Check 7: Assets folder
Write-Host "[7/7] Checking assets..." -ForegroundColor Yellow
if (Test-Path "assets") {
    Write-Host "  ✓ assets folder exists" -ForegroundColor Green
    Write-Host "  ℹ Note: Default icons will be used if custom icons not provided" -ForegroundColor Cyan
} else {
    Write-Host "  ⚠ assets folder not found (will use defaults)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Validation Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✓ All checks passed! Ready to build." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Update API URL in app.json (if needed)" -ForegroundColor White
    Write-Host "  2. Run: .\build-apps.ps1" -ForegroundColor White
    Write-Host "  Or: eas build --platform ios --profile preview" -ForegroundColor White
    exit 0
} else {
    if ($errors.Count -gt 0) {
        Write-Host "✗ ERRORS (must fix before building):" -ForegroundColor Red
        foreach ($error in $errors) {
            Write-Host "  - $error" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "⚠ WARNINGS (recommended to fix):" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    Write-Host "Fix the issues above, then run this script again." -ForegroundColor Yellow
    exit 1
}
