# Git Worktree Setup Script for IoT Security Platform
# This script runs automatically when a new Git worktree is created
# It sets up dependencies and environment variables

Write-Host "`n🚀 Setting up new Git worktree..." -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Get the current directory (worktree root)
$worktreeRoot = $PSScriptRoot
if (-not $worktreeRoot) {
    $worktreeRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}
$projectRoot = Split-Path -Parent $worktreeRoot

Write-Host "📁 Worktree location: $worktreeRoot" -ForegroundColor Gray
Write-Host "📁 Project root: $projectRoot`n" -ForegroundColor Gray

# Check Python installation
Write-Host "🐍 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Python not found! Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
$venvPath = Join-Path $worktreeRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "`n📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "`n📦 Virtual environment already exists" -ForegroundColor Gray
}

# Activate virtual environment
Write-Host "`n🔌 Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Could not activate venv (may need to run manually)" -ForegroundColor Yellow
}

# Install dependencies
$requirementsFile = Join-Path $projectRoot "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "`n📥 Installing Python dependencies..." -ForegroundColor Yellow
    Write-Host "   This may take a minute..." -ForegroundColor Gray
    pip install --upgrade pip --quiet
    pip install -r $requirementsFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to install dependencies" -ForegroundColor Red
    }
} else {
    Write-Host "`n⚠ requirements.txt not found at: $requirementsFile" -ForegroundColor Yellow
}

# Set up .env file
$envExample = Join-Path $projectRoot ".env.example"
$envFile = Join-Path $worktreeRoot ".env"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Write-Host "`n📝 Creating .env file from .env.example..." -ForegroundColor Yellow
        Copy-Item $envExample $envFile
        Write-Host "   ✓ .env file created" -ForegroundColor Green
        Write-Host "   ⚠ Remember to update .env with your actual values!" -ForegroundColor Yellow
    } else {
        Write-Host "`n⚠ .env.example not found. You may need to create .env manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n📝 .env file already exists" -ForegroundColor Gray
}

# Summary
Write-Host "`n✅ Worktree setup complete!" -ForegroundColor Green
Write-Host "================================`n" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review and update .env file with your configuration" -ForegroundColor White
Write-Host "2. Activate virtual environment: .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "3. Run the app: python run.py" -ForegroundColor White
Write-Host "`n" -ForegroundColor White
