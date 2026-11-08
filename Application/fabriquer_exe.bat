@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Lance installer_windows.bat d'abord. & pause & exit /b 1)
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe preparer_reference_dofocus.py
if errorlevel 1 (echo Reference Dofocus invalide. & pause & exit /b 1)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --name Forgely --icon assets\forgely.ico --add-data "assets;assets" --add-data "prices;prices" --add-data "catalogue_dofus3;catalogue_dofus3" forgely.py
pause

