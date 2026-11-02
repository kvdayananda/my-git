@echo off
title GitAuto AI Launcher
echo ==============================================
echo        Starting GitAuto AI Services
echo ==============================================

echo [1/3] Ensuring Docker services (MySQL + Redis) are up...
docker-compose up -d mysql redis

echo [2/3] Launching Backend Server on http://localhost:8000...
start "GitAuto Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --reload --port 8000"

echo [3/3] Launching Frontend Server on http://localhost:3000...
start "GitAuto Frontend (Port 3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ==============================================
echo Both servers are now running in their own windows!
echo Open http://localhost:3000 in your browser.
echo ==============================================
pause

