@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0outils\installer_mise_a_jour_locale.ps1"
if errorlevel 1 echo Installation non terminee. Lis le message ci-dessus.
pause
