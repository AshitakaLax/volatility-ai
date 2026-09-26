# Register the backtest engine host (server/app.py under uvicorn) as a
# Windows scheduled task that starts at boot and stays up.
#
# WHY A SCHEDULED TASK AND NOT A WINDOWS SERVICE
#
# Same reasoning as install_paper_service.ps1: a true service needs a
# wrapper (nssm, pywin32) to host a Python process for no benefit here.
# Task Scheduler's "at startup, restart on failure" trigger is enough.
#
# WHY SYSTEM AND NOT THE CURRENT USER
#
# Unlike the paper-trading loop, this process reads no secrets -- no
# Alpaca keys, no .env. server/app.py's backtest routes only touch the
# warehouse and the local filesystem, so running as SYSTEM (no login
# required, starts before anyone signs in) is strictly simpler than the
# "run whether user is logged on or not" password dance the paper
# service deliberately avoids for a different reason.
#
# WHY RESTART-ON-FAILURE INSTEAD OF A DAILY TRIGGER
#
# This is the opposite shape from the paper loop: that one runs once a
# session and exits by design, this one is meant to never exit. If
# uvicorn dies (OOM kill, an unhandled exception escaping the lifespan),
# Task Scheduler restarts it automatically rather than leaving shards and
# the Pi's web forward silently 502ing until someone notices.
#
# NO CREDENTIALS ARE STORED HERE, because none exist for this process.
#
# Run from an elevated shell -- SYSTEM-context tasks need elevation to
# register, unlike the paper service's current-user task.

param(
    [string]$TaskName = "VolatilityAI-BacktestEngine",
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$BindHost = "0.0.0.0",
    [int]$Port        = 8000,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed scheduled task '$TaskName'."
    exit 0
}

$runner = Join-Path $RepoRoot "tools\run_backtest_engine.cmd"
if (-not (Test-Path $runner)) { throw "Runner not found: $runner" }
if (-not (Test-Path (Join-Path $RepoRoot ".venv\Scripts\python.exe"))) {
    throw "No .venv in $RepoRoot -- run ``uv venv .venv`` and install requirements-web.txt first."
}

$action = New-ScheduledTaskAction -Execute $runner `
    -Argument "`"$BindHost`" `"$Port`"" `
    -WorkingDirectory $RepoRoot

# AtStartup covers a reboot with no one logged in. LogonType ServiceAccount
# (paired with -User SYSTEM below) is what lets it run unattended.
$trigger = New-ScheduledTaskTrigger -AtStartup

# ExecutionTimeLimit 0: this runs indefinitely by design, not a timeout.
# RestartCount/-RestartInterval: bring it back if uvicorn dies; 999 over
# 1-minute intervals is Task Scheduler's practical ceiling for "keep
# trying," which is what an unattended host needs.
# MultipleInstances IgnoreNew: a restart racing the next trigger should
# never produce two uvicorns fighting over one port.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Description `
    "Runs the volatility-ai backtest engine host (server/app.py under uvicorn) bound to $BindHost`:$Port for the Pi's web forward and cli.py shard machines. Restarts automatically at boot and on failure." `
    -Force | Out-Null

Write-Host "Registered '$TaskName': starts at boot, restarts on failure, runs as SYSTEM."
Write-Host "  repo   : $RepoRoot"
Write-Host "  bind   : $BindHost`:$Port"
Write-Host "  log    : $RepoRoot\logs\backtest-engine-<date>.log"
Write-Host ""
Write-Host "  run now : Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  status  : Get-ScheduledTaskInfo -TaskName '$TaskName'"
Write-Host "  stop    : Stop-ScheduledTask -TaskName '$TaskName' -ErrorAction SilentlyContinue; Get-Process python | Where-Object {`$_.Path -like '*volatility-ai*'} | Stop-Process"
Write-Host "  remove  : .\tools\install_backtest_engine_service.ps1 -Remove"
