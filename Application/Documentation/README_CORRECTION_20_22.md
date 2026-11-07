# Forgely 0.20.22 — diagnostic de capture

- Recherche de `Dofus.exe` indépendante du titre de personnage.
- L’observation ne s’arrête plus simplement parce que Forgely ou une autre fenêtre a le focus.
- Le diagnostic OCR affiche désormais `CAPTURE`, avec le nombre de fenêtres candidates, le succès de capture ou le titre brut reconnu.
- Si plusieurs fenêtres DOFUS sont ouvertes et qu’aucune n’a déjà été identifiée, Forgely attend au lieu de choisir une fenêtre arbitrairement.
- La capture MSS reste une capture de l’écran visible : les fenêtres qui recouvrent DOFUS peuvent masquer les pixels du jeu. En mode discret, garder l’atelier visible.
- Ne pas enregistrer de tentative si l’atelier n’est pas confirmé.

**Non validé sur Windows réel.** Cette version améliore l’observabilité et la continuité mais ne garantit pas la reconnaissance OCR sur toutes les échelles d’interface.
