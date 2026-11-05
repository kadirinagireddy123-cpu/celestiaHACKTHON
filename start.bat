@echo off
echo ===================================================
echo Starting Drishti Voice ^& Vision AI Assistant...
echo ===================================================

start "Drishti Backend (FastAPI)" cmd /k "cd /d "%~dp0drishti-build\backend" && python server.py"
start "Drishti Frontend" cmd /k "cd /d "%~dp0drishti-build\frontend" && python -m http.server 8080"

echo Servers starting:
echo   - Backend:  http://localhost:5000
echo   - Frontend: http://localhost:8080
echo Opening frontend in default browser...
start http://localhost:8080

