@echo off
cd /d "%~dp0"
py -3.13 -c "from forgely_catalogue_officiel import charger_catalogue, fiche_objet; print('Objets:',len(charger_catalogue())); print('Exemple:',fiche_objet(44))"
pause
