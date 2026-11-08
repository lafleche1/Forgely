@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Python Launcher introuvable. Installe Python 3.13 puis relance. & pause & exit /b 1)
if not exist .venv\Scripts\python.exe py -3.13 -m venv .venv
if errorlevel 1 (echo Echec creation environnement Python. & pause & exit /b 1)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (echo Echec installation dependances. & pause & exit /b 1)
.venv\Scripts\python.exe preparer_reference_dofocus.py
if errorlevel 1 (echo Reference Dofocus invalide. & pause & exit /b 1)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed --name Forgely --icon "assets\forgely.ico" --add-data "assets;assets" --add-data "prices;prices" --add-data "catalogue_dofus3;catalogue_dofus3" --add-data "catalogue_objets_noms_fr.csv;." --add-data "catalogue_objets_icones.csv;." --add-data "catalogue_runes_officiel.csv;." --add-data "references;references" --add-data "reference_poids_fm.csv;." --add-data "reference_sources_fm.csv;." --add-data "comparaison_modele.csv;." --add-data "videos_sources.csv;." --add-data "walkyrip_sources.csv;." --collect-all pytesseract forgely.py
if errorlevel 1 (echo Echec PyInstaller. & pause & exit /b 1)
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (echo Inno Setup 6 requis : https://jrsoftware.org/isinfo.php & echo Apres installation, relance ce fichier. & pause & exit /b 1)
"%ISCC%" "installateur_forgely.iss"
if errorlevel 1 (echo Echec creation installateur. & pause & exit /b 1)
echo.
echo Installateur cree dans le dossier installateur\
pause
