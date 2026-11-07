@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" exit /b 0
set "PYTHON_CMD="
py -3.13 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1 && set "PYTHON_CMD=py -3.13"
if not defined PYTHON_CMD py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
 echo Python 3.10 ou plus recent est necessaire. Installe Python depuis python.org.
 exit /b 1
)
echo [Forgely] Premiere installation automatique...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
 echo [Forgely] Installation incomplete. Reessaie avec une connexion Internet.
 rmdir /s /q .venv >nul 2>&1
 exit /b 1
)
echo [Forgely] Installation terminee.
exit /b 0
