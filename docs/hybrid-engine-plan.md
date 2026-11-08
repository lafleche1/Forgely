# Intégration hybride — 2026-11-07

Architecture : adaptateur objet autour du moteur DoFocus et de ForgemagingEnv existants. Correcteur en lecture seule de fusion_contexts, appariement exact, prior de 100 observations et seuil de 30 par défaut. Aucun changement de formule DoFocus ni de poids des conseils. Puits inconnu accepté pour représentation/prédiction théorique, refusé pour simulation.

- [x] Tests : repli sans base, exclusion simulation/états différents, lissage, injection du tirage et reproductibilité.
- [x] Implémenter ItemState, TheoreticalEngine, EmpiricalCorrector et DecisionEnvironment.
- [x] Ajouter une distribution optionnelle validée au moteur et un correcteur optionnel à l’environnement existant.
- [x] Vérifier les tests ciblés puis la suite complète. Documenter les limites et l’absence de calibration indépendante réelle.

Résultat : 1306 passed, 24 skipped, 42 subtests passed. TEMP/TMP de test redirigés dans le projet et Tesseract ajouté au PATH du processus de vérification. Aucune modification de la configuration système.
