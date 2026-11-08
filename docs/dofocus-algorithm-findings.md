# Algorithme Dofocus identifié

Analyse du 7 novembre 2026. Source publique chargée par le simulateur :
https://dofocus.fr/assets/index-Do2F7qKb.js

SHA-256 du fichier analysé :
`6a559153678e9394e57da6e92573ef9ae825bacbaf9082b123cc76e68d8110e2`

Le noyau autonome trouvé représente 5 366 caractères de JavaScript minifié.
Le code tiers complet reste dans les fichiers temporaires de recherche ; il
n'est pas ajouté au code distribué de Forgely.

## Fonctions identifiées

| Fonction | Responsabilité |
|---|---|
| `Pz` | Plafonds, régime, difficulté et chances SC/SN/EC |
| `cqe` | Qualité pondérée des autres lignes naturelles |
| `uqe`, `dqe` | Difficulté normale/over et répartition des résultats |
| `fqe` | Traitement des lignes exotiques et de cas particuliers |
| `gqe` | Pertes de caractéristiques, consommation et création de reliquat |
| `vqe` | Tirage d'une tentative et nouvel état complet |

La difficulté utilise le niveau, le poids/gain de rune, la valeur actuelle,
la position dans les bornes naturelles, la qualité des autres lignes et l'over.
Le puits intervient dans la résolution des pertes ; le calcul `Pz` observé
ne reçoit pas le reliquat comme entrée. Certains résultats exotiques sont
explicitement signalés comme estimés.

## Vérification exécutée

Exécution isolée du noyau public, sans appel au jeu ou au serveur Dofocus.
Anneau du Cycloïde niveau 200, preset moyen :
Vitalité 276, Force/Intelligence/Agilité 36, dommages neutre/terre/feu/air 9,
Initiative 251, résistance eau 7 %, Tacle 5.

Pour une rune Fo : SC 2 %, SN 46,90973185943033 %, EC 51,09026814056967 %.
Ces valeurs reproduisent l'affichage observé du site : 2 / 47 / 51.

## Portée de la découverte

Le moteur de simulation Dofocus est présent côté navigateur et son fonctionnement
peut être étudié. Ce constat ne démontre pas qu'il s'agit de l'algorithme officiel
d'Ankama.

## Intégration réalisée

Le modèle local est implémenté dans `Application/forgely_dofocus_engine.py` et
raccordé aux conseils via `forgely_simulation_live.py`. La parité couvre 359 cas
de calcul et 1 077 transitions déterministes, dont naturel, over, exos, malus,
niveaux et plafonds. Aucun JavaScript distant n'est exécuté par l'application.

Les chances sont calculées directement ; 48 essais par rune affinent ensuite
l'exposition aux pertes sur un worker dédié. Les résultats restent attachés au
jet complet, au puits et aux objectifs exacts. Les simulations sont conservées
dans un journal distinct, avec compteurs réel/simulé/total. Les accès au journal
restent hors du thread de l'interface.
