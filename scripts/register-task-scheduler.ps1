<#
.SYNOPSIS
    Installs a Windows Scheduled Task for GitAuto AI Daily Local GitHub Backup.
.DESCRIPTION
    Configures Windows Task Scheduler to run scripts\backup-daily.ps1 daily at a specified time.
.PARAMETER TaskName
    Name of the scheduled task (default: GitAutoDailyBackup).
.PARAMETER Time
    Daily execution time in 24-hour HH:mm format (default: 02:00).
.PARAMETER DryRun
    If specified, configures the task to run in Dry-Run mode.
#>

[CmdletBinding()]
param(
    [string]$TaskName = "GitAutoDailyBackup",
    [string]$Time = "02:00",
    [switch]$DryRun
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BackupScript = Join-Path $ScriptDir "backup-daily.ps1"

if (-not (Test-Path $BackupScript)) {
    Write-Error "Could not find backup script at: $BackupScript"
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   GitAuto AI - Windows Task Scheduler Setup              " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Task Name: $TaskName"
Write-Host "Schedule:  Daily at $Time"
Write-Host "Script:    $BackupScript"
Write-Host "Dry-Run:   $($DryRun.IsPresent)"

$dryRunArg = if ($DryRun) { "-DryRun" } else { "" }
$actionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`" $dryRunArg"

try {
    # Check if task already exists
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "`nUpdating existing scheduled task '$TaskName'..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "GitAuto AI Daily Local GitHub Backup automation" | Out-Null

    Write-Host "`n[SUCCESS] Windows Scheduled Task '$TaskName' registered successfully!" -ForegroundColor Green
    Write-Host "Backups will automatically execute every day at $Time."
    Write-Host "Logs will be recorded in: backend\logs\backups\daily_backup.log"
} catch {
    # Fallback to schtasks.exe if PowerShell cmdlets require elevated permissions
    Write-Host "`nAttempting registration via schtasks.exe fallback..." -ForegroundColor Yellow
    $schArgs = "/create /tn `"$TaskName`" /tr `"powershell.exe $actionArgs`" /sc daily /st $Time /f"
    Start-Process -FilePath "schtasks.exe" -ArgumentList $schArgs -Wait -NoNewWindow
    Write-Host "`nTask Scheduler configuration completed via schtasks." -ForegroundColor Green
}

