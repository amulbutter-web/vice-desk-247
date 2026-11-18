@echo off
title Vice Desk - 0.001% Gaming Content Intelligence Studio
echo =====================================================================
echo  Starting Vice Desk Private Publish Studio (0.001% Precision Engine)
echo =====================================================================
echo.
echo  Studio URL: http://localhost:8000
echo  API Documentation: http://localhost:8000/docs
echo.

"C:\Users\rudra\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn src.server.app:app --host 0.0.0.0 --port 8000 --reload
pause
