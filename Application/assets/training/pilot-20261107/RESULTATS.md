# Premier entraînement Forgely — 7 novembre 2026

Entraînement terminé en 27,14 secondes : 3 000 épisodes, 20 824 tentatives
de runes virtuelles, 237 états agrégés appris par Q-learning.

Anneau du Cycloïde niveau 200, jet initial médian, 36 Force, 36 Intelligence,
puits initial 10. Objectif : 40 Force et 40 Intelligence simultanément.
Limite : 30 tentatives par épisode. Les autres caractéristiques ne sont pas
des objectifs de conservation dans cette expérience.

Évaluation après entraînement sur 500 nouvelles graines par stratégie :

| Stratégie | Objectif atteint | Tentatives moyennes par session | Récompense moyenne |
|---|---:|---:|---:|
| Apprise | 464/500 — 92,8 % | 9,196 | 54,212 |
| Petites runes, plus grand déficit d'abord | 333/500 — 66,6 % | 24,384 | 40,506 |
| Rune autorisée au hasard, sans arrêt volontaire | 477/500 — 95,4 % | 13,632 | 55,604 |

Les moyennes de tentatives incluent toutes les sessions, y compris les échecs.
La stratégie apprise s'arrête volontairement sans atteindre l'objectif dans
36 sessions. Le hasard atteint la limite de tentatives dans 23 sessions.
Le modèle appris utilise moins de tentatives, mais ne surpasse pas le hasard
sur la réussite ni sur la récompense moyenne dans cette évaluation.
Ces résultats sont descriptifs, sans démonstration de supériorité statistique.

Il s'agit exclusivement de simulations du modèle local Dofocus, pas de taux
observés dans DOFUS. Aucun prix fourni : aucune conclusion de rentabilité en
kamas. Un seul objet et un seul départ ont été entraînés. L'agrégation des états
perd des détails. La politique expérimentale n'est pas activée dans les conseils
en direct et aucun résultat virtuel n'est ajouté aux observations réelles.

`policy.json` contient les valeurs apprises et les nombres de visites ;
`metrics.json` contient les paramètres et les mesures. `reproduce.py` se relance
depuis le projet Forgely avec son environnement Python pour reproduire l'essai.
