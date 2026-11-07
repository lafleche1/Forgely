# Forgely 0.20.25 — capture de DOFUS

- Conserve la détection du jeu par nom de processus et par titre versionné.
- Compare le HWND de premier plan avec la fenêtre racine du jeu (les sous-fenêtres Unity sont acceptées).
- Quand Forgely a le focus, tente PrintWindow sur le HWND DOFUS au lieu de capturer Forgely avec mss.
- Rejette les captures natives noires/uniformes et ne transmet pas ces images à l'OCR.
- En cas de capture GPU indisponible, repasser sur DOFUS : la capture écran standard reste utilisable.

Attention : PrintWindow n'est pas garanti pour le rendu GPU de DOFUS. Validation terrain Windows nécessaire.
