# Correction locale : comparaison des runes de finition

Base : Forgely v22.16 présente dans C:\Users\genef\Documents\ChatGPT\Forgely le 10 novembre 2026. Aucun remplacement par une ancienne archive ni téléchargement de version. Ce dossier ne contient pas de dépôt Git exploitable ; les fichiers existants ont été sauvegardés avant retouche dans before/, et les empreintes avant/après figurent dans manifest.json.

## Correction appliquée

- Une Pa/Ra de finition légale peut être examinée même lorsqu'il ne reste qu'un objectif à terminer.
- Une réserve couverte n'est plus préférée automatiquement à une réparation naturelle : sa progression nominale plafonnée au minimum, multipliée par le taux SC+SN du modèle partagé calibré, doit dépasser les autres finitions de la même ligne. Le classement entre réserves utilise le poids des caractéristiques ; le poids de rune départage les égalités.
- Les restrictions de densité, les profils incomplets, les objectifs déjà atteints, les priorités de réparation des lignes lourdes et les séquences simulées restent contrôlés.
- Les actions de l'entraîneur incluent les mêmes finitions couvertes et les Pa exposées déjà admises près du maximum. Les versions de politique et du sélecteur changent : aucune ancienne politique n'est présentée comme validée avec ces nouvelles actions. Aucun entraînement long n'a été lancé et aucune base d'observations n'a été modifiée.

## Médaille Kido : distinction nécessaire

Le catalogue local equipment_bounds.csv donne Sagesse 31–40. Les trois runes sont comparées : Sa +1 / poids 3 ; Pa Sa +3 / poids 9 ; Ra Sa +10 / poids 30. Depuis 38, elles visent respectivement 39, 41 et 48. Le garde-fou existant autorise la ligne naturelle à 40, mais refuse un over dont la densité totale dépasse 101. À 41 sagesse, la densité est 123 ; à 48, elle est 144. Le puits 61 n'annule pas cette contrainte. Le moteur conserve donc Sa dans ce cas et explique l'exclusion des deux autres tailles. Cette correction ne prétend pas démontrer une règle serveur ni contourner le garde-fou existant.

Un dépassement du minimum est accepté lorsqu'il respecte les limites physiques : avec un maximum naturel de 60, Sagesse 38 / minimum 40 peut être terminée à 41 par Pa Sa. Intelligence 39 / minimum 40 / maximum naturel 40 peut aussi être terminée à 42 par Pa Ine : densité 42, sous 101. La rune n'est jamais imposée sans comparaison.

Exemples réduits à une seule ligne, niveau 125, puits 61 (modèle provisoire, pas taux réels mesurés sur la capture complète) :

| État | Résultat du moteur |
|---|---|
| Sagesse 38, minimum 40, naturel 40 | Sa ; Pa/Ra exclues par densité |
| Sagesse 38, minimum 40, naturel 60 | Pa Sa |
| Intelligence 39, minimum/naturel 40 | Pa Ine (17,708 % SC+SN contre 17 % pour Ine) |
| Intelligence 39, minimum 40, naturel 60 | Pa Ine |

Sans niveau fourni, le même exemple Intelligence naturel 40 conserve Ine (17 % contre 16,770 % pour Pa Ine). Les tests vérifient aussi que des observations vérifiées favorables à la rune simple, Pa ou Ra changent effectivement le choix. Ces données de test sont synthétiques.

## Observations locales vérifiées

Lecture seule de C:\Users\genef\AppData\Local\Forgely\observations_locales.sqlite3 via le chargeur existant : 71 transitions qualifiées au total ; aucune transition qualifiée pour l'objet 7136 (Médaille Kido). Il n'y a donc pas de taux empirique propre à cet objet à annoncer. Le modèle reste provisoire. La calibration exige au moins 30 observations vérifiées comparables et conserve le lissage existant.

Les indicateurs de progression sont nominaux : les gains partiels en SN et les pertes collatérales exactes ne sont pas connus dans cette comparaison. Le poids hors puits reste une exposition, et non une perte moyenne inventée. Le prix des runes reste soumis au contrat existant du moteur : priorité au jet complet, pas optimisation monétaire nouvelle.

## Fichiers modifiés

Production :
- Application/forgely_decision.py
- Application/forgely_predictive.py
- Application/forgely_rl.py
- Application/forgely_training.py

Tests :
- Tests/test_finish_tier_comparison.py (nouveau, 15 cas)
- Tests/test_minimum_targets.py
- Tests/test_cycloide_recommendation.py
- Tests/test_rl_environment.py
- Tests/test_sequence_planning.py
- Tests/test_reserve_over.py
- Application/tests/test_fm_objectives.py

Les anciens tests qui imposaient l'exclusion d'une Pa de finition légale ou une priorité absolue à Pa Vi ont été adaptés au comportement demandé. Les tests de reproductibilité, de légalité et de priorité restent actifs. changes.diff contient les différences ; manifest.json contient les empreintes.

## Vérification

Les tests ciblés ont été exécutés après observation initiale de trois échecs reproduisant les défauts. Les tests ciblés finaux couvrent les changements de taux, les différents paliers, la densité sagesse, le budget de puits, l'entraîneur et la conservation des priorités.

La suite complète utilise un dossier temporaire situé dans le projet et le Tesseract déjà installé dans C:\Program Files\Tesseract-OCR. Le premier lancement était affecté par le dossier temporaire Windows inaccessible, puis par Tesseract absent du chemin de recherche ; aucun changement de code OCR n'a été nécessaire. Les sorties finales sont dans tests.txt et tests.xml.

Résultat final de la suite complète : **2332 tests réussis, 27 ignorés, 42 sous-tests réussis**, aucun échec (144,83 secondes). Les 15 cas du nouveau fichier sont inclus. Les empreintes des 11 fichiers modifiés ont été revérifiées après les tests.
