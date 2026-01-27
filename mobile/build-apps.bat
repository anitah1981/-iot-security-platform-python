@echo off
echo ========================================
echo   IoT Security Mobile App Builder
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Checking EAS CLI installation...
where eas >nul 2>&1
if %errorlevel% neq 0 (
    echo EAS CLI not found. Installing...
    call npm install -g eas-cli
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install EAS CLI
        pause
        exit /b 1
    )
) else (
    echo EAS CLI found!
)
echo.

echo [2/4] Checking login status...
eas whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo Not logged in. Please login:
    call eas login
    if %errorlevel% neq 0 (
        echo ERROR: Login failed
        pause
        exit /b 1
    )
) else (
    echo Already logged in!
)
echo.

echo [3/4] Checking project configuration...
if not exist "eas.json" (
    echo Configuring project...
    call eas build:configure
    if %errorlevel% neq 0 (
        echo ERROR: Configuration failed
        pause
        exit /b 1
    )
) else (
    echo Project already configured!
)
echo.

echo [4/4] Ready to build!
echo.
echo Choose platform:
echo   1. iOS (iPhone)
echo   2. Android
echo   3. Both
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Building iOS app...
    call eas build --platform ios --profile preview
) else if "%choice%"=="2" (
    echo.
    echo Building Android app...
    call eas build --platform android --profile preview
) else if "%choice%"=="3" (
    echo.
    echo Building iOS app...
    call eas build --platform ios --profile preview
    echo.
    echo Building Android app...
    call eas build --platform android --profile preview
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Check the output above for download links.
echo.
pause
