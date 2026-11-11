# Continuité du copilote pendant les masquages

Demande : conserver l’objet, son jet souhaité et les conseils lorsqu’une infobulle,
Forgely ou une autre application masque DOFUS. Réidentifier l’objet seulement
lorsque son icône change réellement.

## Comportement retenu

- Une icône momentanément illisible ne supprime plus l’identité ni les objectifs.
- Une icône identique conserve l’identité, même si l’OCR du nom ou des bornes
  naturelles varie. Le texte d’une infobulle ne renomme pas l’objet.
- Une nouvelle icône doit apparaître sur trois captures distinctes et cohérentes
  avant de déclencher le parcours existant d’identification et de définition du
  nouveau jet souhaité.
- Pendant le masquage, le dernier conseil calculé reste affiché. Son cache est
  uniquement en mémoire et lié à l’objet, à l’objectif et au mode de conseil.
- Dès que des lectures complètes se stabilisent, le jet réel et le puits sont
  actualisés et les conseils recalculés, sans réidentifier la même icône.
- Une fois la lecture confirmée, la relance périodique toutes les douze secondes
  est désactivée pour ce contexte d’atelier. La comparaison visuelle et les
  demandes de confirmation d’un changement restent actives.
- Au retour d’un masquage, les zones utiles strictement identiques à celles de
  la dernière lecture confirmée réutilisent cette lecture sans OCR. Les images
  réellement capturées continuent à confirmer la stabilité ; aucun faux scan
  ni événement de rune n’est fabriqué.
- Les zones du jet et du puits sont aussi réutilisées individuellement si leurs
  pixels sont inchangés : une sélection de rune ou un changement d’historique
  ne force donc pas à relire des chiffres déjà confirmés. Une zone modifiée
  perd immédiatement cette réutilisation.
- L’observateur ne bascule pas automatiquement sur un autre atelier simplement
  parce que celui de l’objet déjà identifié est temporairement illisible.

Les calculs conservés pendant le masquage reposent sur le dernier jet confirmé.
Aucune évolution cachée du jet n’est inventée.

La pose d’une rune signifie ici un changement observé de l’historique, du jet
ou du puits dans DOFUS. Le survol ou la sélection d’une rune ne constitue pas
une tentative de forgemagie. Aucun nouveau jet souhaité n’est demandé pour ces
actions lorsque l’icône de l’objet reste identique.

## Apprentissage et contexte

Les instantanés OCR, appariements avant/après et contextes d’apprentissage sont
invalidés lors d’un masquage. Le conseil affiché n’est jamais une observation
réelle ni une nouvelle donnée d’entraînement. Les règles strictes de
`current_snapshot` restent intactes. Une tentative effectivement détectée
déclenche toujours sa lecture après fusion.

Un arrêt explicite de l’observation, un changement de fenêtre/compte ou de
dimensions conserve les protections de changement de contexte existantes.
Les masquages n’entraînent aucun clic automatique ni changement de premier plan.

## Fichiers

- `Application/forgely.py` : conservation de session, traitement des masquages,
  remplacement confirmé de l’icône et reprise des lectures.
- `Application/forgely_copilot_continuity.py` : confirmation visuelle du changement
  et réutilisation du conseil affiché sous le même objectif ; lecture d’atelier
  confirmée conservée en mémoire sous son contexte et ses pixels sources.
- `Application/forgely_zone_cache.py` : réutilisation durable des seules zones
  numériques effectivement confirmées et strictement inchangées.
- `Tests/test_copilot_occlusion.py` : régression avec la véritable application Tk,
  reprise du jet/puits, remplacement d’icône, captures distinctes et objectif édité.
- `Tests/test_confirmed_reading_reuse.py` : absence d’OCR et de relance périodique
  sur les lectures confirmées, invalidation sur changement de zone ou de compte,
  et vérification du branchement dans l’observateur réel.
- Deux tests existants de capture ont été adaptés aux nouvelles dépendances de
  leur montage de test (image réelle et classe de lecture confirmée).

Sauvegarde : `.test-tmp/forgely-before-occlusion-fix-20261108.py`.
Sauvegarde du cache de zones :
`.test-tmp/forgely-zone-cache-before-confirmed-reuse-20261108.py`.
Modifications locales uniquement ; aucun envoi GitHub.

## Vérification

Le test initial reproduisait la perte d’identité après `atelier_waiting`.
La correction de masquage seule a passé 1 734 tests, 26 ignorés et 42 sous-tests
dans `.test-tmp/occlusion-full-03.log`. La réutilisation des lectures inchangées
est vérifiée ensuite dans `.test-tmp/reuse-full-final.log` : **1 740 tests
réussis, 31 ignorés, 42 sous-tests réussis, aucune erreur, code de sortie 0**.
Les 18 vérifications ciblées finales (masquage, réutilisation et identification
rapide) passent aussi. Les tests ignorés ne constituent pas une validation.

Les masquages ont été simulés dans les tests ; une session de jeu avec plusieurs
applications superposées n’a pas été pilotée pour cette vérification.
