# Diagnostic Anneau du Cycloïde — 10 novembre 2026

## Version utilisée

Dossier confirmé par l’utilisateur : C:\Users\genef\Documents\ChatGPT\Forgely.
Ce dossier n’a pas de métadonnées Git : aucune branche ni équivalence avec GitHub ne peut être certifiée. Les sources decision/predictive étaient datées du 10 novembre, plus récentes que la fusion documentée du 8 novembre. Aucun téléchargement, remplacement depuis GitHub ou push. Sauvegarde des deux fichiers avant modification : .tmp/cycloide-before.

## Capture et reproduction

La capture jointe a été ouverte. DOFUS affiche lui-même « reliquat : 4,3 » ; Forgely affiche la même valeur. Cela ne démontre ni un puits réel de zéro, ni un OCR périmé. Il manque une chronologie complète pour arbitrer la contradiction avec le joueur. Le suivi exact exige une base lue et des transitions complètes, sans trou ; aucune modification du suivi du puits n’a été faite sans défaut reproduit.

Jet intégral transcrit : Vitalité 288, Force 38, Intelligence 40, Agilité 38, Dommages Neutre 6, Terre 10, Feu 10, Air 8, Initiative 146, Résistance Eau 7 %, Tacle 5.
Les quatre cibles visibles (300/40/40/40) reproduisent Vi, à puits 0 comme à puits 4,3. Les cibles des lignes masquées ne sont pas connues : en supposant toutes les lignes au maximum naturel, le conseil devient Pa Do Neutre à zéro et Tac à 4,3. La capture ne permet donc pas de reconstituer tout le plan enregistré.

## Causes

1. La génération exclut Pa Vi et Ra Vi avant classement : leurs gains nominaux conduiraient à 303 et 338, au-delà du maximum 300. C’est une politique conservatrice contre un over non demandé, pas une impossibilité de pose.
2. Le plan de consommation nominale du puits pouvait remplacer une séquence complète déjà classée. Un test reproduit Pa Fo remplacée par Fo avec un puits de 1. Corrigé : les séquences comparables passent avant ce plan nominal.
3. Le modèle provisoire place Vi à SC 2 / SN 15 / EC 83 dans ce cas. Son terme de difficulté dépend du ratio jet/gain et ses planchers expliquent ces nombres. Ce ne sont pas des mesures serveur. Le seuil communautaire de palier ne constitue pas une preuve d’impossibilité.

## Comparaison sans prix

Les poids locaux versionnés issus d’une extraction tierce du client donnent Vi +5/poids 1, Pa Vi +15/poids 3, Ra Vi +50/poids 10 ; vitalité 0,2 par point. Les tests existants vérifient leur cohérence entre les entrées du moteur. La provenance n’est pas une validation officielle Ankama, ni une nouvelle extraction du client du jour.

Pour le jet intégral de la capture, niveau 200, les estimations du modèle sont :

| Rune | SC / SN / EC (%) | Gain utile nominal moyen, plafonné à 300 | Exposition hors puits 0 / 4,3 | Valeur nominale |
|---|---|---|---|---|
| Vi | 2 / 15 / 83 | 0,850 vitalité | 1 / 0 | 293 |
| Pa Vi | 2 / 6,416 / 91,584 | 1,010 vitalité | 3 / 0 | 303 |
| Ra Vi | 2 / 19,316 / 78,684 | 2,558 vitalité | 10 / 5,7 | 338 |

Gain utile nominal moyen = min(gain, déficit) × (SC + SN). Il surestime le gain si SN est partiel, et ignore les pertes : ce n’est PAS une espérance nette. L’exposition n’est pas une perte moyenne, et zéro exposition ne garantit pas la protection d’un over. Sans distribution fiable des gains partiels et des lignes dégradées, ni classement optimal ni supériorité de Pa/Ra ne sont démontrés. Aucun coefficient de probabilité n’a été inventé ou retouché pour imposer une réponse.

## Modifications

- forgely_predictive.py : conserve la priorité des séquences vers le jet complet avant les plans nominaux de puits.
- forgely_decision.py : expose tier_comparison pour tous les paliers des lignes incomplètes, même exclus ; probabilités provisoires, gain utile nominal moyen, exposition, valeur résultante et motif d’exclusion. Espérance nette explicitement inconnue. Explication visible des paliers exclus de la ligne sélectionnée.
- Tests/test_cycloide_recommendation.py : reproduction des quatre cibles visibles et du profil intégral, puits 0/4,3, autres jets saturés, absence de probabilités officielles et régression de priorité de séquence.

Les gardes contre l’over non demandé restent en place : le conseil Vi peut donc subsister. Cette livraison corrige la priorité et la transparence ; elle ne prétend pas résoudre l’optimisation nette du jet complet. Autoriser automatiquement 303 ou 338 sans validation du modèle de pertes serait un changement supplémentaire non justifié par cette capture.

## Validation

Avant correction : 5 tests de comparaison échouent par absence de diagnostic ; test distinct de priorité échoue avec Fo à la place de Pa Fo.
Après correction : 98 tests réussis et 1 ignoré sur le premier groupe (poids, affichage, audit, relecture de puits, actualisation) ; 81 réussis sur le second groupe après les dernières modifications (13 nouveaux cas, décision, matrices, séquences, plans, registre/observateur de puits, probabilités). Les groupes se recoupent : ne pas additionner comme un total unique.
Un premier lancement avait 3 erreurs de création de fichiers temporaires ; relance réussie avec un répertoire temporaire dans le projet. Pas de suite globale ni de mesure en jeu revendiquée.

Commande de reproduction ciblée :

    .\.venv\Scripts\python.exe -m pytest -q --basetemp=.tmp\cycloide-reproduction Tests\test_cycloide_recommendation.py

Validation finale regroupée sur les fichiers finaux : 168 réussis, 1 ignoré, en 8,72 secondes. Aucun échec.
