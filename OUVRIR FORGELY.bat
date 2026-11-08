@echo off
setlocal
cd /d "%~dp0Application"
if exist "%~dp0.venv\Scripts\python.exe" (
 "%~dp0.venv\Scripts\python.exe" "forgely.py"
 if errorlevel 1 pause
 exit /b
)
if not exist ".venv\Scripts\python.exe" (
 call "installer_windows.bat"
 if errorlevel 1 (
  echo.
  echo Impossible de preparer Forgely. Lis le message ci-dessus.
  pause
  exit /b 1
 )
)
".venv\Scripts\python.exe" "forgely.py"
if errorlevel 1 (
 echo.
 echo Forgely s'est arrete avec une erreur.
 pause
)
