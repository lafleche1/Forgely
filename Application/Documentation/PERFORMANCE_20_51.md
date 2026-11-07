# Forgely v20.52 — optimisation expérimentale

Base : v20.50 stable. Aucune modification des règles de confirmation de jet, de reliquat ou d'identification par logo.

- Intervalle entre deux cycles d'observation : 1,2 s → 0,35 s (hors durée de capture/OCR).
- Cache OCR par zone pour historique, effets, runes et reliquat. Comparaison exacte des pixels et relecture forcée après 3 secondes, ou dès que l'atelier n'est plus reconnu.
- Chronométrage borné en mémoire de la capture, de la lecture atelier/OCR et de l'extraction d'icône (p50/p95/p99).
- Le titre de l'atelier est toujours relu ; l'interface Dofus reste inchangée.

## Vérification

Six tests ciblés réussis. Suite historique de 205 tests : 2 échecs préexistants également observés sur v20.50 (un test de recadrage d'icône et un libellé d'attente), 4 ignorés.

Les gains réels de latence ne sont pas encore mesurés sur Windows. Cette version est expérimentale et peut consommer davantage de CPU. Conserver v20.50 pour revenir à la version stable.
