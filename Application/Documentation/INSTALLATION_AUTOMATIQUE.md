# Forgely — installation intelligente (préparation Windows)

Le fichier final `Forgely-Setup-0.20.15.exe` est fabriqué sur Windows avec `fabriquer_installateur_windows.bat`. Le programme Python et ses bibliothèques sont **embarqués** dans l’exécutable : l’utilisateur n’a pas à installer Python ni pip.

Au lancement de l’installateur, le script `installation/verifier_prerequis.ps1` :

1. Cherche Tesseract OCR dans le PATH et dans les dossiers usuels. S’il existe, il **ne le réinstalle pas**.
2. Si Tesseract est absent, tente une installation silencieuse via `winget` (paquet UB-Mannheim.TesseractOCR).
3. Vérifie la langue française `fra`. Si elle manque, télécharge uniquement son modèle dans `%LOCALAPPDATA%\Forgely\tessdata` ; l’anglais existant est copié si disponible.
4. Écrit le journal dans `%LOCALAPPDATA%\Forgely\installation-ocr.log`.

**Limites :** cette installation dépend d’un accès Internet et de `winget` pour ajouter Tesseract. Une élévation Windows peut être demandée. Si l’installation OCR échoue, Forgely reste installable et utilisable hors OCR ; consulter le journal. Les téléchargements OCR doivent être sécurisés par vérification de signature ou d’empreinte avant diffusion publique. Le comportement doit être validé sur Windows 10/11 avant distribution. Aucun `.exe` compilé n’est fourni dans cette archive.

Le serveur, PostgreSQL et Docker ne sont **pas** installés sur les PC des joueurs.
