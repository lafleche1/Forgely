# Réactivité de Forgely — mesures du 7 novembre 2026

Optimisations appliquées dans le projet local :

- Reconnaissance des icônes : caractéristiques des références réutilisées et calcul des différences dans Pillow. Les distances et seuils de rejet restent identiques.
- Conseils : une lecture groupée des observations remplace les requêtes répétées pour chaque rune. Pas de cache persistant de ces statistiques ; le conseil suivant relit les données enregistrées.
- Interface : un seul minuteur de rafraîchissement des statistiques ; les rafraîchissements manuels n'ajoutent plus de boucles périodiques.
- Entraînement : les actions valides sont calculées sans construire le vecteur complet d'état inutilisé à cet endroit.
- OCR : récupération réussie de la première ligne réutilisée pour des pixels identiques pendant huit secondes, avec cache limité ; un changement de pixels force une nouvelle lecture.
- Historique : expressions des noms de runes préparées une fois par catalogue ; chaque nouveau texte OCR reste analysé indépendamment.

## Mesures locales

| Opération | Avant | Après | Méthode |
|---|---:|---:|---|
| Comparaison des 105 références d'icônes | 115,39 ms | 17,40 ms | Médiane de cinq passages |
| Statistiques de 30 runes sur 30 000 observations synthétiques | 208,99 ms | 16,95 ms | Médiane de trois passages ; 30 connexions deviennent une |
| Lecture textuelle du nom de rune, 2 000 appels | 1 222,51 ms | 52,24 ms | Meilleur de trois lots ; catalogue complet |
| Entraînement Cycloïde, 20 sessions de 60 actions maximum + évaluations | 1 818,81 ms | 1 782,49 ms | Un passage par version ; résultats et table Q identiques à graine fixée |
| Relecture directe d'effets identiques, récupération de Vitalité déjà réussie | 237,8 ms | 9,67 ms | Médiane de douze passages, capture de test réelle |

L'écart de l'entraînement complet est faible et peut relever de la variation d'exécution ; il ne faut pas extrapoler le gain de la validation des actions à tout l'entraînement. Le cache de zone évitait déjà l'OCR complet sur une zone inchangée : le gain de récupération concerne les appels qui passent encore par le lecteur d'effets.

La capture réelle, les changements d'interface et l'OCR d'une image nouvelle restent dépendants de DOFUS, du processeur et de la visibilité de l'atelier. Ces micro-mesures ne démontrent pas un délai global inférieur à une seconde en jeu. La pondération 40 % simulations / 60 % observations réelles et les règles de confirmation des lectures sont conservées.
