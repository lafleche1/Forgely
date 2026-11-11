@echo off
setlocal
cd /d "%~dp0Application"
if exist "..\.venv\Scripts\python.exe" (
  "..\.venv\Scripts\python.exe" entrainer_forgely.py
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" entrainer_forgely.py
) else (
  echo L'environnement Forgely est introuvable. Lance d'abord OUVRIR FORGELY.bat.
  pause
  exit /b 1
)
if errorlevel 1 pause
