@echo off
setlocal
cd /d "%~dp0"

echo ======================================================================
echo    FORGELY (COPIE BUREAU) - TEST D'ACQUISITION NDI / OBS STUDIO
echo ======================================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "outils\test_ndi_capture.py" %*
    if errorlevel 1 (
        echo.
        echo Le script s'est arrete avec un code erreur.
        pause
    )
    exit /b 0
)

echo [ERREUR] L'environnement virtuel .venv est introuvable.
pause
exit /b 1
