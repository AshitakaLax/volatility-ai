@echo off
REM The backtest engine host: server/app.py under uvicorn, bound to the
REM LAN so the Pi's `web` service can forward /api/backtest/* (and, unless
REM VAI_BACKTEST_UPSTREAM points elsewhere, /api/ml/*) here, and so
REM `cli.py shard` machines have something to register against. See
REM docs/DEPLOY_RASPBERRY_PI.md, "Running sweeps on more than one machine".
REM
REM Long-lived by design, unlike run_paper_session.cmd -- this does not
REM exit on its own. The scheduled task's restart settings are what bring
REM it back after a crash or reboot.
REM
REM Usage: run_backtest_engine.cmd [host] [port]

setlocal enabledelayedexpansion
cd /d "%~dp0.."

set "HOST=%~1"
if "%HOST%"=="" set "HOST=0.0.0.0"
set "PORT=%~2"
if "%PORT%"=="" set "PORT=8000"

if not exist ".venv\Scripts\python.exe" (
    echo [runner] .venv\Scripts\python.exe not found -- run `uv venv .venv` and install requirements-web.txt first. 1>&2
    exit /b 2
)

if not exist "logs" mkdir "logs"
for /f %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%D"
set "LOG=logs\backtest-engine-%TODAY%.log"

echo [runner] %DATE% %TIME% starting backtest engine on %HOST%:%PORT% >> "%LOG%"
".venv\Scripts\python.exe" cli.py serve --host %HOST% --port %PORT% >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo [runner] %DATE% %TIME% engine exited with %RC% >> "%LOG%"
exit /b %RC%
