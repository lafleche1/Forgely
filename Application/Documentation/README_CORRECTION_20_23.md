# Forgely 0.20.23 — correction ciblée de la détection

- Énumération native des fenêtres Windows via EnumWindows et signatures 64 bits, sans dépendre de l'énumération de pygetwindow.
- Association automatique à Dofus.exe et repli sur le titre DOFUS 3 quand la lecture du processus est interdite.
- Le diagnostic conserve le titre de la fenêtre détectée même avant la confirmation de l'atelier.
- La capture mss est une capture du bureau : elle est donc **refusée** lorsque DOFUS n'est pas au premier plan, afin de ne plus analyser Forgely comme si c'était le jeu.

## Limites restantes

Cette correction n'est pas une capture directe du rendu de DOFUS : les fenêtres superposées peuvent masquer des pixels. Laisser l'atelier visible, DOFUS au premier plan, et placer l'overlay hors de l'atelier. Aucune validation en situation réelle sur le PC de l'utilisateur n'a été possible.
