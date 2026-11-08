@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Lance installer_windows.bat d'abord. & pause & exit /b 1)
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe preparer_reference_dofocus.py
if errorlevel 1 (echo Reference Dofocus invalide. & pause & exit /b 1)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --name Forgely --icon assets\forgely.ico --add-data "assets;assets" --add-data "prices;prices" --add-data "references/poids_runes_client_3_7_13_17.json;references" --add-data "catalogue_dofus3;catalogue_dofus3" --add-data "catalogue_objets_noms_fr.csv;." --add-data "catalogue_objets_icones.csv;." --add-data "catalogue_runes_officiel.csv;." --add-data "references;references" --add-data "reference_poids_fm.csv;." --add-data "reference_sources_fm.csv;." --add-data "comparaison_modele.csv;." --add-data "videos_sources.csv;." --add-data "walkyrip_sources.csv;." forgely.py
pause
