# Forgely 0.19.2 — Interface simplifiée

Cette version reprend le moteur local de Forgely 0.19.1 et simplifie uniquement la fenêtre principale.

## Visible en permanence
- État de la détection DOFUS et bouton Démarrer / Arrêter
- Prochaine rune suggérée (ou « jet à lire » si les informations sont incertaines)
- Équipement suivi et bouton de sélection rapide
- Dernière action et nombre de tentatives locales
- Mode discret et bouton Plus

## Dans « Plus »
Historique, outils/kamas, diagnostic OCR, apprentissage des runes, import de catalogue, paramètres et sauvegarde. Toutes les fonctions existantes restent accessibles.

## Installation
Comme la version précédente : installer_windows.bat puis demarrer_forgely.bat. Python 3.13 et Tesseract français sont nécessaires. La version reste 100 % locale pour les données de jeu.

## Limites
La reconnaissance visuelle de DOFUS reste expérimentale. Aucun taux de réussite ne sera inventé et Forgely doit attendre une lecture fiable après chaque rune. Les tests de code ne remplacent pas un test sur Windows avec le jeu actif.
