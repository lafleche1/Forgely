# Forgely — fabriquer un installateur Windows

## Résultat attendu

Le fichier `installateur/Forgely-Setup-0.20.15.exe` installe Forgely sans demander Python à l'utilisateur final, crée une entrée dans le menu Démarrer et peut créer un raccourci sur le Bureau. Le logo officiel déjà inclus dans `assets/forgely.ico` est utilisé pour l'exécutable, l'assistant d'installation et les raccourcis.

## Préparation (sur Windows 10/11 64 bits)

1. Installer Python 3.13 64 bits depuis python.org (avec `py` disponible).
2. Installer Inno Setup 6 depuis https://jrsoftware.org/isinfo.php.
3. Extraire tout le ZIP dans un dossier normal (éviter OneDrive si possible).
4. Double-cliquer sur `fabriquer_installateur_windows.bat` et attendre la fin.
5. Récupérer `installateur/Forgely-Setup-0.20.15.exe`.

Le script installe les dépendances, construit une application autonome avec PyInstaller et emballe le résultat avec Inno Setup. Les images du catalogue de runes sont incluses. Le serveur communautaire n'est pas nécessaire pour lancer l'application.

## Important

- **L'installateur EXE n'est pas inclus dans ce ZIP** : il doit être compilé sur Windows. Le script et les fichiers nécessaires sont fournis.
- L'OCR dépend de **Tesseract OCR**, qui doit être installé séparément sur le PC utilisateur (langue française incluse). L'installateur Forgely ne l'installe pas automatiquement.
- Ce programme n'est pas signé numériquement ; Windows SmartScreen peut afficher un avertissement. Ne contourner cet avertissement que si vous faites confiance à la provenance du fichier.
- Tester l'installateur sur une autre session Windows avant toute distribution. Les tests unitaires ne garantissent pas que le paquet Windows démarre correctement.
- Les données personnelles de Forgely sont conservées dans `%LOCALAPPDATA%\Forgely` et ne sont pas supprimées automatiquement à la désinstallation.
