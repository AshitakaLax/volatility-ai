# Register the paper-trading supervisor as a daily Windows scheduled task.
#
# WHY A SCHEDULED TASK AND NOT A WINDOWS SERVICE
#
# A true service needs a wrapper (nssm, pywin32) to host a Python
# process, runs in Session 0 where nothing is visible, and adds a
# dependency for no benefit here. The workload is "start once a
# weekday morning and exit after the close" -- which is what Task
# Scheduler is for.
#
# WHY THE TRIGGER IS EARLY AND VAGUE
#
# It fires at 06:00 LOCAL on weekdays and the supervisor does the real
# thinking. It asks Alpaca when the market opens, sleeps until then,
# sizes the session, and exits after the close -- so holidays,
# half-days, and DST shifts are all handled by the broker's own
# calendar rather than by this trigger. Getting the trigger "right" is
# neither possible nor necessary: it only has to be early enough.
#
# Weekdays only is an optimisation, not the correctness boundary. On a
# holiday the task still fires and the supervisor exits in two seconds.
#
# NO CREDENTIALS ARE STORED HERE. The task runs a .cmd that loads .env
# itself, so key material stays in that file and never enters the task
# definition, the registry, or this script.
#
# Run from an ordinary shell -- registering a task for the CURRENT user
# needs no elevation. Elevation would only be needed for -User SYSTEM,
# which is wrong here anyway: the loop needs the user's .env.

param(
    [string]$TaskName = "VolatilityAI-PaperTrading",
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Config   = "config/paper_aggressive.yaml",
    [string]$StateDb  = "paper_ledger.db",
    [string]$StartAt  = "06:00",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Removed scheduled task '$TaskName'."
    exit 0
}

$runner = Join-Path $RepoRoot "tools\run_paper_session.cmd"
if (-not (Test-Path $runner)) { throw "Runner not found: $runner" }
if (-not (Test-Path (Join-Path $RepoRoot ".env"))) {
    throw "No .env in $RepoRoot -- the runner needs APCA_API_KEY_ID / APCA_API_SECRET_KEY."
}

# The .cmd is the Execute target directly -- NOT wrapped in cmd.exe /c.
#
# `cmd.exe /c "script" "arg"` strips the outer quotes when the first
# token after /c is quoted, and the remainder parses as a request for an
# INTERACTIVE shell. The task then "runs", sits there, and reports
# failure with nothing in the log -- observed exactly that, LastTaskResult
# 1 and an empty log file, because the runner's first line never
# executed. Task Scheduler runs a .cmd through the shell association
# without needing the wrapper at all.
$action = New-ScheduledTaskAction -Execute $runner `
    -Argument "`"$Config`" `"$StateDb`"" `
    -WorkingDirectory $RepoRoot

$trigger = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $StartAt

# StartWhenAvailable covers a machine that was asleep at 06:00 -- it
# runs late, and the supervisor works out how much session is left and
# declines if there is not enough.
#
# ExecutionTimeLimit 0 means no timeout: a session legitimately runs
# ~6.5 hours and Task Scheduler's default would kill it partway.
#
# MultipleInstances IgnoreNew stops a second copy trading the same
# account if a run somehow overlaps the next trigger.
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 0

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description `
    "Runs the volatility-ai paper trading loop for one market session. The task fires early; the supervisor asks Alpaca when the market actually opens and exits after the close, so holidays and DST need no schedule changes." `
    -Force | Out-Null

Write-Host "Registered '$TaskName': weekdays at $StartAt local."
Write-Host "  repo   : $RepoRoot"
Write-Host "  config : $Config"
Write-Host "  log    : $RepoRoot\logs\paper-<date>.log"
Write-Host ""
Write-Host "  run now : Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  status  : Get-ScheduledTaskInfo -TaskName '$TaskName'"
Write-Host "  remove  : .\tools\install_paper_service.ps1 -Remove"
