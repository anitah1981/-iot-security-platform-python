@echo off
echo ========================================
echo   Pre-Build Validation
echo ========================================
echo.

cd /d "%~dp0"

echo [1/7] Checking EAS CLI...
where eas >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] EAS CLI installed
) else (
    echo   [ERROR] EAS CLI not found. Run: npm install -g eas-cli
    set ERRORS=1
)
echo.

echo [2/7] Checking Expo login...
eas whoami >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Logged in
) else (
    echo   [WARNING] Not logged in. Run: eas login
    set WARNINGS=1
)
echo.

echo [3/7] Checking project configuration...
if exist "eas.json" (
    echo   [OK] eas.json exists
) else (
    echo   [WARNING] eas.json not found. Run: eas build:configure
    set WARNINGS=1
)
echo.

echo [4/7] Checking app.json...
if exist "app.json" (
    echo   [OK] app.json exists
    echo   [INFO] Check API URL in app.json before building
) else (
    echo   [ERROR] app.json not found!
    set ERRORS=1
)
echo.

echo [5/7] Checking dependencies...
if exist "node_modules" (
    echo   [OK] node_modules exists
) else (
    echo   [WARNING] node_modules not found. Run: npm install
    set WARNINGS=1
)
echo.

echo [6/7] Checking required files...
if exist "App.js" (
    echo   [OK] App.js exists
) else (
    echo   [ERROR] App.js missing!
    set ERRORS=1
)
if exist "package.json" (
    echo   [OK] package.json exists
) else (
    echo   [ERROR] package.json missing!
    set ERRORS=1
)
echo.

echo [7/7] Checking assets...
if exist "assets" (
    echo   [OK] assets folder exists
) else (
    echo   [INFO] assets folder not found (will use defaults)
)
echo.

echo ========================================
echo   Validation Summary
echo ========================================
echo.

if defined ERRORS (
    echo [ERRORS] Fix errors above before building!
    pause
    exit /b 1
) else if defined WARNINGS (
    echo [WARNINGS] Review warnings above, then proceed.
    echo.
    echo Ready to build? Run: build-apps.bat
    pause
    exit /b 0
) else (
    echo [SUCCESS] All checks passed! Ready to build.
    echo.
    echo Next steps:
    echo   1. Update API URL in app.json if needed
    echo   2. Run: build-apps.bat
    pause
    exit /b 0
)
