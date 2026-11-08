@echo off
cd /d "%~dp0"
echo Ferme Forgely avant de continuer.
pause
if exist "Application\.venv\Scripts\python.exe" (
  "Application\.venv\Scripts\python.exe" "outils\mettre_a_jour_prix_tylezia.py" "%~dp0."
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python "outils\mettre_a_jour_prix_tylezia.py" "%~dp0."
  ) else (
    py -3 "outils\mettre_a_jour_prix_tylezia.py" "%~dp0."
  )
)
if errorlevel 1 (
  echo La mise a jour n'a pas abouti. Lis le message ci-dessus.
) else (
  echo Tu peux relancer Forgely.
)
pause
