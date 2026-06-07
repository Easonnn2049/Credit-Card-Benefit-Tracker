@echo off
setlocal
cd /d "%~dp0"

echo.
echo ================================================
echo Credit Card Benefit Tracker - server check
echo ================================================
echo.

echo Port 8501:
netstat -ano | findstr :8501

echo.
echo Local health:
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing -TimeoutSec 5; Write-Output ('127.0.0.1 health: ' + $r.StatusCode + ' ' + $r.Content) } catch { Write-Output ('127.0.0.1 health ERROR: ' + $_.Exception.Message) }"

echo.
echo Current Wi-Fi IPv4 candidates:
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | ForEach-Object { '  http://' + $_.IPAddress + ':8501/?mobile=true' }"

echo.
echo Recent Streamlit log:
if exist tmp\streamlit-8501.log (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -LiteralPath 'tmp\streamlit-8501.log' -Tail 40"
) else (
    echo No tmp\streamlit-8501.log yet.
)

echo.
pause
