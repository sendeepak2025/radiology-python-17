@echo off
echo === Kiro-mini Network Configuration ===
echo.

echo Detecting your machine's IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    set IP=!IP: =!
    echo Found IP: !IP!
    goto :found
)

:found
if "%IP%"=="" (
    echo Could not detect IP address automatically.
    set /p IP="Please enter your machine's IP address: "
)

echo.
echo Selected IP: %IP%
echo.

echo Updating configuration files...

REM Update frontend .env
if exist "frontend\.env" (
    powershell -Command "(Get-Content 'frontend\.env') -replace 'REACT_APP_API_URL=.*', 'REACT_APP_API_URL=http://%IP%:8000' | Set-Content 'frontend\.env'"
    powershell -Command "(Get-Content 'frontend\.env') -replace 'REACT_APP_WS_URL=.*', 'REACT_APP_WS_URL=ws://%IP%:8000' | Set-Content 'frontend\.env'"
    powershell -Command "(Get-Content 'frontend\.env') -replace 'REACT_APP_ORTHANC_URL=.*', 'REACT_APP_ORTHANC_URL=http://%IP%:8042' | Set-Content 'frontend\.env'"
    echo ✓ Updated frontend/.env
) else (
    echo ✗ Frontend .env file not found
)

echo.
echo === Configuration Complete ===
echo.
echo Your Kiro-mini application is now configured to use IP: %IP%
echo.
echo Access URLs:
echo   Frontend:  http://%IP%:3000
echo   Backend:   http://%IP%:8000
echo   Orthanc:   http://%IP%:8042
echo.
echo Next steps:
echo   1. Restart Docker containers: docker-compose down ^&^& docker-compose up -d
echo   2. Access the application from any device on your network
echo.
pause