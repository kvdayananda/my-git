<#
.SYNOPSIS
    GitAuto AI - Daily Local GitHub Backup Script for Windows.
.DESCRIPTION
    Runs safe daily backups for configured GitAuto AI local projects.
    Excludes .env, credentials, and secrets.
    Verifies remote commit SHA.
    Supports dry-run and retries.
.PARAMETER ProjectId
    Optional ID of a specific local project to back up. If omitted, backs up all active projects.
.PARAMETER DryRun
    If specified, scans and previews files without pushing remote commits.
.PARAMETER ApiUrl
    GitAuto AI API endpoint (default: http://localhost:8000).
#>

[CmdletBinding()]
param(
    [int]$ProjectId = 0,
    [switch]$DryRun,
    [string]$ApiUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
$LogDir = Join-Path $RootDir "backend\logs\backups"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$LogFile = Join-Path $LogDir "daily_backup.log"
$Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

function Write-BackupLog {
    param([string]$Message, [string]$Level = "INFO")
    $line = "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

Write-BackupLog "=========================================================="
Write-BackupLog "Starting GitAuto AI Daily Backup Automation"
Write-BackupLog "Mode: $(if ($DryRun) { 'DRY-RUN (Simulated)' } else { 'LIVE BACKUP' })"
Write-BackupLog "Target Backend: $ApiUrl"

# Verify API is reachable
try {
    $health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get -TimeoutSec 10
    Write-BackupLog "GitAuto AI backend is healthy and responding."
} catch {
    Write-BackupLog "ERROR: GitAuto AI backend is not running at $ApiUrl. Aborting backup run." "ERROR"
    exit 1
}

# Fetch projects to back up using the system/local endpoints
try {
    $projectsUrl = "$ApiUrl/api/v1/backups/projects"
    # Using python runner or direct curl with session
    Write-BackupLog "Executing backup run for ProjectId=$($ProjectId) (DryRun=$DryRun)..."
    
    $pythonCmd = @"
import asyncio
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if os.path.abspath(".") not in sys.path:
    sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import LocalProject, User
from app.services.backup.engine import execute_backup

async def main():
    db = SessionLocal()
    try:
        query = select(LocalProject).where(LocalProject.is_active == True)
        if $ProjectId > 0:
            query = query.where(LocalProject.id == $ProjectId)
        projects = db.scalars(query).all()
        if not projects:
            print("No active projects found to back up.")
            return

        for p in projects:
            user = db.get(User, p.user_id)
            if not user:
                continue
            print(f"--> Processing backup for project #{p.id}: {p.name} ({p.local_path})")
            for attempt in range(1, 4):
                try:
                    record = await execute_backup(project=p, user=user, db=db, dry_run=bool('$DryRun'.lower() == 'true'))
                    print(f"    Status: {record.status} | Commit SHA: {record.commit_sha or 'N/A'}")
                    if record.status in ('success', 'dry_run', 'skipped_no_changes'):
                        break
                    print(f"    Retry {attempt}/3 due to status={record.status}")
                except Exception as exc:
                    print(f"    Attempt {attempt}/3 failed: {exc}")
                    if attempt < 3:
                        await asyncio.sleep(2 * attempt)
    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(main())
"@
    
    $tempPy = Join-Path $env:TEMP "gitauto_run_backup.py"
    $pythonCmd | Set-Content -Path $tempPy -Encoding UTF8

    $backendDir = Join-Path $RootDir "backend"
    Push-Location $backendDir
    $prevPythonPath = $env:PYTHONPATH
    $env:PYTHONPATH = $backendDir
    $output = python $tempPy 2>&1
    $env:PYTHONPATH = $prevPythonPath
    Pop-Location
    Remove-Item $tempPy -Force -ErrorAction SilentlyContinue

    foreach ($msg in $output) {
        Write-BackupLog "$msg"
    }

    Write-BackupLog "Daily Backup Automation execution finished successfully."
    Write-BackupLog "=========================================================="

} catch {
    Write-BackupLog "Exception encountered during daily backup: $_" "ERROR"
    exit 1
}
