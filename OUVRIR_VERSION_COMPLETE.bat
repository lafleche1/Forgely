@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0distribution\restaurer_version_complete.ps1"
if errorlevel 1 echo La restauration a echoue. Aucun dossier de travail existant n est remplace.
pause
