# Essais des overs temporaires — 8 novembre 2026

Prototype isolé dans .test-tmp/over-ablation-20261108. 24 entraînements principaux et 6 variantes élargies terminés. Par condition et par objet : deux graines d’entraînement, chacune 512 épisodes, puis 500 évaluations indépendantes (1 000 au total). Limite de 150 poses par évaluation. Objectif : atteindre toutes les cibles, sans récompense pour fabriquer du puits.

| Cas | Témoin | Over temporaire limité à 3 PWR | Témoin → candidat : poses moyennes |
|---|---:|---:|---:|
| Cycloïde, objectifs demandés | 729/1 000 | 720/1 000 | 94,66 → 95,37 |
| Cycloïde, finition | 998/1 000 | 999/1 000 | 12,68 → 13,43 |
| Bague Gloursonne, finition | 763/1 000 | 679/1 000 | 67,85 → 75,88 |
| Anneau de Brouce, PO absent | 937/1 000 | 890/1 000 | 47,09 → 53,95 |
| Alliance Gloursonne | 734/1 000 | 622/1 000 | 92,19 → 102,98 |
| Gelano exo PM, témoin sans ligne préparatoire | 546/1 000 | 546/1 000 | 105,49 → 105,49 |

Variante élargie à 10 PWR et plusieurs tailles : Cycloïde demandé 690/1 000, Bague Gloursonne 711/1 000, Brouce 896/1 000, contre les mêmes témoins. Pas d’amélioration globale démontrée. L’écart 998 → 999 ne justifie pas un gain : il ne représente qu’un succès supplémentaire sur 1 000 et davantage de poses.

## Limites et décision

Ces résultats concernent le modèle local Dofocus, ses approximations de pertes et sa limite de puits, pas le serveur du jeu. Deux graines d’entraînement ne démontrent pas une généralisation universelle. Le prototype apprend une exploration limitée ; il ne reproduit pas toutes les stratégies des meilleurs forgemages. Des tests de parité ont vérifié que l’optimisation technique du prototype ne changeait pas les transitions ni les résultats de son témoin.

La stratégie reste envisageable, conformément à la demande de l’utilisateur : elle doit être étudiée selon l’objet et la situation, avec des vidéos fiables. Ne pas la transformer en règle obligatoire et ne pas créditer artificiellement le puits avant une perte observée. Aucun de ces essais simulés n’a été transmis aux observations réelles.

Données détaillées : .test-tmp/over-ablation-20261108/summary.json, main/results.json et broader/results.json. Les politiques expérimentales portent une version distincte et ne sont pas chargées comme conseils actifs.
