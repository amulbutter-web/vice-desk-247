@echo off
title GTA 6 Vice Desk - 24/7 Production Supervisor
cd /d "%~dp0"

echo ======================================================================
echo    GTA 6 VICE DESK - 24/7 PRODUCTION SUPERVISOR & CLOUDFLARE TUNNEL
echo ======================================================================
echo.
echo [1/3] Checking Python 3.13 Environment...
set PYTHON_BIN=C:\Users\rudra\AppData\Local\Programs\Python\Python313\python.exe
if not exist "%PYTHON_BIN%" set PYTHON_BIN=python

echo [2/3] Initializing Database & Ensuring Schema...
"%PYTHON_BIN%" -m src.cli init

echo [3/3] Engaging 24/7 Process Supervisor & Cloudflare Edge Tunnel...
echo.
echo ----------------------------------------------------------------------
echo  * Local URL:  http://localhost:8000
echo  * Public URL: Look for '>>> 24/7 VICE DESK PUBLIC LIVE LINK' below!
echo  * Security:   Cloudflare Edge SSL (100% Free Forever | Zero Attack Surface)
echo ----------------------------------------------------------------------
echo.

"%PYTHON_BIN%" -m src.supervisor.daemon

pause
