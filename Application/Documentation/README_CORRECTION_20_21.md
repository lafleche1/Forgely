# Forgely 0.20.21 — Reconnaissance du processus Dofus.exe

Cette version corrige la récupération du nom du processus associé à une fenêtre Windows en déclarant explicitement les types des fonctions Win32 (handles compatibles Windows 64 bits).

- Détection automatique des fenêtres appartenant à `Dofus.exe`, indépendamment du nom du personnage.
- Repli prudent sur le titre du jeu si Windows refuse la lecture du processus.
- Refus des autres processus (Chrome, etc.), même avec un titre trompeur.
- Mode discret conservé, sans sélection manuelle.
- Trois nouveaux tests automatisés, 145 tests au total.

## Essai sur Windows

Fermer Forgely, extraire l'archive dans un nouveau dossier, puis double-cliquer sur `demarrer_forgely.bat`. Ouvrir DOFUS et son atelier, activer l'observation, passer en mode discret. Le diagnostic OCR doit afficher le nom de la fenêtre DOFUS et des lectures positives. Si « Fenêtre : Non détectée » persiste, noter si DOFUS est au premier plan lorsque le test se déroule.

Limite : la capture utilise toujours `mss` et peut être masquée par des fenêtres superposées. Aucun test Windows réel n'a été réalisé dans cet environnement.
