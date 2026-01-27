@echo off
echo ========================================
echo Starting Expo for iPhone (LAN Mode)
echo ========================================
echo.

REM Get IP address
echo Getting your IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo.
    echo Your IP address: !IP!
    echo.
    echo ========================================
    echo IN EXPO GO APP:
    echo ========================================
    echo 1. Open Expo Go on your iPhone
    echo 2. Tap "Enter URL manually"
    echo 3. Type: exp://!IP!:8081
    echo 4. Tap "Connect"
    echo ========================================
    echo.
    echo Starting Expo...
    echo.
)

REM Start Expo with LAN mode
call npm run start:lan
