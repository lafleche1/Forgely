# Forgely 0.20.24 — restauration de la détection par titre

La détection de la fenêtre DOFUS accepte désormais soit le processus Dofus.exe, soit un titre caractéristique de DOFUS 3 tel que `Agglou - Pandawa - 3.7.13.17 - Release`, même si Windows retourne un nom de processus inattendu. Les fenêtres de Forgely restent exclues.

## Limites

La capture `mss` reste une capture des pixels visibles de l'écran. Pour vérifier la reconnaissance, laissez DOFUS au premier plan et l'atelier visible. Le programme ne peut pas garantir une lecture correcte si le jeu est masqué. La correction est testée automatiquement mais pas encore validée sur votre PC Windows.

## Vérification

Lancer `installer_windows.bat` puis `demarrer_forgely.bat`, ouvrir DOFUS et activer l'observation. Dans Diagnostic OCR, vérifier FENÊTRE, CAPTURE et LECTURES.
