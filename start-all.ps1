Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "       Starting GitAuto AI Services           " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }

Write-Host "`n[1/3] Ensuring Docker services (MySQL + Redis) are up..." -ForegroundColor Yellow
docker-compose up -d mysql redis

Write-Host "`n[2/3] Launching Backend on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; python -m uvicorn app.main:app --reload --port 8000"

Write-Host "`n[3/3] Launching Frontend on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm run dev"

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host "Both servers have been launched in separate windows!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "==============================================" -ForegroundColor Green

