# Simulateur dynamique connecté au copilote

Le simulateur du dépôt utilise désormais le même moteur que les conseils : `forgely_decision.candidates` et `forgely_predictive`. À chaque clic virtuel il recalcule la rune, Q, difficulté, seuil 80 %, pression ×14, over, niveau et effets d'exos. Les comptages réels qualifiés peuvent calibrer les taux par contexte exact. Aucun tirage virtuel ne rejoint ces comptages.

## Dans l'application

Ouvrir « Stratégies, données & réussites », puis « Simuler mon objectif ». L'objet, le jet stable, les minima, maxima naturels, niveau éventuel, prix et budget RESTANT sont capturés au lancement. Changer l'objet pendant le travail ne change pas cette simulation. Le worker ne lit aucun widget Tk. Fermer la fenêtre demande l'annulation entre deux clics. De 1 à 2000 sessions, au plus 100 clics par session dans l'interface.

Sans données suffisantes, le rapport indique les transitions inconnues au lieu de prétendre connaître le jet suivant. Les bornes affichées valent réussites/trials et (réussites+sessions inconnues)/trials, pour l'horizon et les gardes retenus. Ce n'est pas un intervalle de confiance statistique ou une probabilité garantie en jeu. Un arrêt au budget ou à la limite de clics n'est pas une réussite. Le coût moyen compte chaque rune effectivement tirée, même celle dont les pertes restent inconnues ; il est limité au préfixe simulé et n'est pas un coût final estimé des sessions interrompues.

## Puits et transitions

- SC : gain nominal, puits inchangé.
- SN : gain nominal puis pertes éventuelles, y compris sur la ligne ciblée.
- EC : aucun gain puis pertes éventuelles.
- Après pertes connues : max(0, puits initial + densité perdue − densité de la rune), en comptant toutes les lignes. Le puits n'est pas plafonné à 101.
- Un puits insuffisant n'interdit pas une tentative. Le moteur comptabilise la rune puis utilise un vecteur réel de pertes, une approximation demandée ou arrête la transition comme inconnue.
- Des overs/exos existants rendent les pertes incertaines même avec un puits élevé. Leurs priorités et les limites de ce que la recherche a établi sont dans [RECHERCHE_PERTES_FM.md](RECHERCHE_PERTES_FM.md).

La banque empirique filtre `source=local_screen`, `calibration_verified=1`, SN/EC, puis vérifie à nouveau la cohérence des gains/pertes/puits. L'échantillonnage conserve l'objet, le jet complet exact, le puits exact, la rune et l'issue. Sans correspondance, aucune donnée d'un autre objet n'est réutilisée par défaut.

Le choix « Pertes approximatives » poursuit des scénarios sans données en tirant uniformément des lignes positives dans les groupes de priorité. Ce modèle simplifié ne connaît pas les pondérations serveur et ne doit pas servir à affirmer un coût optimal ou à produire des statistiques réelles.

## Ligne de commande

Créer un contexte JSON, par exemple :

```json
{"item":"Exemple fictif","jets":{"Force":0},"targets":{"Force":20},"natural_max":{"Force":100},"pool":50,"level":169,"prices":{"Fo":36,"Pa Fo":132,"Ra Fo":382},"mode":"Budget optimisé","budget":10000,"profile_complete":true}
```

Puis :

```sh
python Application/laboratoire_fm.py --contexte contexte.json --sessions 100 --limite 100
python Application/laboratoire_fm.py --contexte contexte.json --pertes uniform --sessions 100
python Application/laboratoire_fm.py --contexte contexte.json --base-reelle observations_locales.sqlite3
```

L'API `simulate_item` et le job UI/CLI utilisent les mêmes calculs, reproductibles par seed. Le maximum d'un appel est un million de clics virtuels. Le mode historique fixe est conservé par `simulate_target` et `laboratoire_fm.py --manuel` ; ses résultats ne deviennent pas des taux dynamiques.

## Portée de la mise à jour

Il s'agit des sources de l'application et de son laboratoire présents dans ce dépôt. Aucun moteur externe `Forgely-entrainement.exe` absent des sources n'a été modifié. Il n'y a pas de nouvel agent RL ni de policy apprise injectée automatiquement dans le copilote. Cette modification fournit un environnement de simulation cohérent avec le modèle probabiliste accepté, dont la fidélité des pertes reste bornée par les données disponibles.

Les profils contenant des malus sont refusés avec un message explicite : les transitions négatives ne sont pas encore modélisées. Les gardes propres à l’objet (limites de lignes et runes bloquées dans les contextes documentés) sont partagées avec le conseil.
