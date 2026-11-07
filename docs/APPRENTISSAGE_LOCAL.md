# Apprentissage automatique local

Les transitions avant/après capturées par l'observateur sont conservées en SQLite et relues au démarrage. Le laboratoire en arrière-plan fournit maintenant au moteur de conseils un ajustement du classement, activé automatiquement sans service distant ni dépendance supplémentaire.

L'apprentissage ne mélange pas objets, runes ou jets observés différents. Le puits est regroupé par les classes existantes. Il faut au moins 30 transitions admissibles par contexte. Les sources simulées sont exclues. Chaque transition doit conserver les mêmes lignes, présenter le gain nominal pour SC/SN, aucune hausse pour EC, aucune hausse sur une autre ligne et un puits cohérent avec les poids connus. Les malus et poids inconnus sont exclus.

L'ajustement utilise les gains SC/SN observés avec un lissage de 30 observations neutres. Son facteur reste entre 0,8 et 1,2. Il modifie uniquement le classement après les contrôles de légalité, de lecture et de budget. L'explication indique le nombre de transitions et le facteur appliqué. Avant le seuil, le moteur conserve son comportement initial.

Il s'agit d'une adaptation statistique explicable, pas du réentraînement d'un réseau neuronal. La cohérence des lectures ne constitue pas une validation indépendante de l'OCR. Les caractéristiques non visibles, les classes larges de puits et la sélection des tentatives peuvent biaiser les données. Un EC sans changement à puits nul est conservé uniquement lorsqu'un nouvel événement de l'historique a été confirmé. Les événements manqués par l'observateur restent absents. Les fréquences ne sont pas des probabilités du jeu et l'amélioration du rendement reste à mesurer sur des sessions réelles. Chaque session peut enrichir la base si des transitions exploitables sont reconnues ; chaque session ne garantit pas une modification ou une amélioration du conseil.

Pour conserver l'apprentissage, conserver le dossier de données local utilisé par Forgely. Aucune capture, donnée de session ou base personnelle n'est incluse dans les sources publiées.
