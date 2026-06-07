@echo off
setlocal
cd /d "%~dp0"

title Credit Card Benefit Tracker - local Streamlit server

if not exist tmp mkdir tmp
set LOG_FILE=tmp\streamlit-8501.log

echo.
echo ================================================
echo Credit Card Benefit Tracker
echo Local Streamlit server
echo ================================================
echo.
echo This window must stay open while you use the app.
echo If your phone keeps loading, close the phone tab and reopen the Network URL below.
echo.

echo Checking for an old server on port 8501...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8501 .*LISTENING"') do (
    echo Stopping old process %%P on port 8501...
    taskkill /PID %%P /F >nul 2>&1
)

echo.
echo Starting Streamlit on port 8501...
echo Log file: %LOG_FILE%
echo.
echo Phone URL candidates:
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | ForEach-Object { '  http://' + $_.IPAddress + ':8501/?mobile=true' }"
echo.
echo If your Wi-Fi IP changes, use the Network URL printed by Streamlit below.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "& py -m streamlit run app.py 2>&1 | Tee-Object -FilePath '%LOG_FILE%'"
pause
