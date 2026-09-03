@echo off
REM One paper-trading session. Invoked by the scheduled task.
REM
REM This exists so the task definition never holds credentials: the keys
REM stay in .env and are loaded here, into this process only. A task
REM definition is stored in the registry and dumped in plain text by
REM Get-ScheduledTask, so an API key placed there would be sitting in
REM two more places than it needs to be.
REM
REM Usage: run_paper_session.cmd [config] [state-db]

setlocal enabledelayedexpansion
cd /d "%~dp0.."

set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=config/paper_aggressive.yaml"
set "STATE_DB=%~2"
if "%STATE_DB%"=="" set "STATE_DB=paper_ledger.db"

if not exist ".env" (
    echo [runner] .env not found in %CD% -- cannot load Alpaca credentials. 1>&2
    exit /b 2
)

REM Load KEY=VALUE lines, skipping blanks and comments. Values are never
REM echoed: `set` inside a for loop would print them without @echo off,
REM and this file is read by whoever debugs the task.
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "LINE=%%A"
    if not "!LINE!"=="" if not "!LINE:~0,1!"=="#" set "%%A=%%B"
)

if not exist "logs" mkdir "logs"
for /f %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%D"
set "LOG=logs\paper-%TODAY%.log"

echo [runner] %DATE% %TIME% starting session: %CONFIG% >> "%LOG%"
python tools\market_hours_supervisor.py --config "%CONFIG%" --state-db "%STATE_DB%" >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo [runner] %DATE% %TIME% supervisor exited with %RC% >> "%LOG%"
exit /b %RC%
