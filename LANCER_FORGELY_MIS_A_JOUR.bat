@echo off
cd /d "%~dp0Application"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" forgely.py
) else if exist "..\.venv\Scripts\python.exe" (
  "..\.venv\Scripts\python.exe" forgely.py
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python forgely.py
  ) else (
    py -3 forgely.py
  )
)
if errorlevel 1 (
  echo Forgely n'a pas demarre. Lis le message ci-dessus.
  pause
)
