# Malus : règles trouvées et validation restante

Recherche du 10 novembre 2026, pour DOFUS PC 3.7.13.17. Les règles de Touch,
Rétro et serveurs privés ne sont pas transposées au jeu courant.

## Résultats documentaires

| Point | Résultat | Source et portée |
|---|---|---|
| Coût d'une pose sur statistique négative | Le guide indique un demi-poids, avec exception pour -1 → 0 au poids normal. Le coût de pose n'est pas une loi du choix des pertes. | [Guide Gamosaurus](https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus), collaboration Florelsan, modification indiquée au 9 juillet 2023 ; source communautaire, pas formule serveur publiée. |
| Reliquat | Les densités retirées et celle de la rune expliquent sa variation ; le puits est affiché dans l'atelier actuel. | [Guide de Huz](https://huzounet.fr/guides/forgemagie), daté du 30 septembre 2026. Il ne fournit pas d'algorithme complet des pertes signées. |
| Poids des malus et éligibilité des lignes | Le guide contient un tableau distinct et décrit un lien entre le ciblage des malus, leur niveau de remontée et le nombre de lignes. Les valeurs ne justifient pas un facteur universel appliqué à toutes les pertes. | [Guide Tofus](https://www.tofus.fr/fiches/forgemagie), non daté ; plusieurs valeurs et exemples sont anciens. Ne pas utiliser comme table active 3.7.13.17. |

## Ce qui n'est pas établi pour tous les profils courants

- Répartition des points perdus entre plusieurs lignes négatives/positives.
- Probabilité qu'une ligne donnée soit sélectionnée lors d'un SN ou d'un EC.
- Formule de tous les franchissements de zéro avec des paliers multipoins.
- Table complète et versionnée des poids des effets négatifs de la version PC.
- Limites exactes de dégradation et comportement de chaque malus amélioré.

Des guides anciens se contredisent sur la transformation d'un malus en bonus.
Un résultat de simulateur ne tranche pas cette divergence pour DOFUS PC courant.
Aucune garantie de légalité propre aux lignes signées n'est ajoutée au conseiller.
Les gardes positives connues restent appliquées, et une contrainte non vérifiable
reste explicitement signalée dans son explication.

## Référence locale de recherche

`forgely_dofocus_legacy.py` reproduit un ancien simulateur tiers. Son coût de
tentative est réduit si la valeur projetée reste strictement négative ; son
traitement des pertes contient aussi un facteur 0.5 sur certaines lignes.
Cela décrit ce simulateur, pas les règles officielles du serveur. Ce code
archivé n'a pas été reconnecté aux conseils ni aux observations réelles.

## Données locales consultées

Lecture seule de la base native `observations_locales.sqlite3` : 71 transitions
avant/après disponibles, aucune contenant un malus et aucune transition Tétriste.
Elles ne permettent donc pas de calibrer ces règles. Aucune observation n'a été
ajoutée, corrigée ou supprimée par cette recherche.

## Mise en œuvre retenue

Le conseiller accepte les lectures et cibles signées et classe les runes connues
selon leurs gains nominaux vers la cible, sans probabilités signées extrapolées
ni simulation automatique. Le débit futur du puits sur SN/EC signé reste inconnu.
Un tel transfert ne peut plus être calculé avec les poids des lignes positives :
la lecture directe du reliquat reste la référence. Les SC cohérents conservent
le puits. Les observations réellement capturées restent distinctes des hypothèses.

Pour compléter la validation, une vidéo de session avec jet, puits, historique
et rune lisibles permettra d'annoter les états successifs et de tester les règles
documentées sur des exemples observés. Les passages proches de zéro, les paliers
et les pertes sur malus remontés sont particulièrement informatifs. Une session
unique ne permet pas de déduire toutes les probabilités serveur.
