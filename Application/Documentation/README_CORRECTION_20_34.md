# Forgely 0.20.34 — Correction de l’identification d’objet

- Correction de l’OCR du nom d’objet : le petit logo à gauche pouvait être lu comme `73` lors du second passage OCR, faisant rejeter un nom correct.
- Le nom et le logo restent soumis à plusieurs captures cohérentes avant inscription locale.
- Le mini-overlay ne dit plus « Attente 1re rune » lorsque l’historique OCR contient déjà des échecs ou réussites : il affiche « Objet à identifier ».
- Pas de modification de la détection de fenêtre, de la capture, du titre d’atelier ou du démarrage en un clic.
- Aucune tentative ancienne n’est réinterprétée comme une nouvelle tentative.

Limite : les résultats OCR sur le PC Windows et les changements de l’interface DOFUS nécessitent encore une validation terrain.
