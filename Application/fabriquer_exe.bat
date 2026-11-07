@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Lance installer_windows.bat d'abord. & pause & exit /b 1)
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --name Forgely --icon assets\forgely.ico --add-data "assets;assets" forgely.py
pause
