# Forgely 0.20.20 — Détection automatique et mode discret

- Détection des fenêtres DOFUS par nom de processus lorsque Windows le permet, avec repli sur le titre du jeu (personnage / classe / version).
- Plus de sélection manuelle dans le menu Plus.
- Mémorisation automatique de la dernière fenêtre détectée pendant la session.
- Le mini-overlay Forgely peut prendre le focus sans suspendre la capture.
- Lecture suspendue lorsqu’une autre application est au premier plan, pour éviter de capturer des données étrangères au jeu.
- Si plusieurs fenêtres DOFUS sont ouvertes et qu’aucune n’est identifiable avec certitude, l’analyse se met en attente plutôt que de choisir arbitrairement.

**Limite :** `mss` photographie l’écran visible. Une fenêtre qui recouvre DOFUS peut masquer des zones OCR. Cette version n’a pas été validée sur un PC Windows réel.
