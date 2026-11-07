@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Lance d'abord installer_windows.bat
 pause
 exit /b 1
)
.venv\Scripts\python.exe forgely.py
if errorlevel 1 pause
