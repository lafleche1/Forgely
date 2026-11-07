# Forgely 0.20.2 — validation prédictive externe

Le nouveau laboratoire `laboratoire_validation_predictive.py` teste les fréquences SC/SN/EC **sur des tentatives chronologiquement postérieures à l’entraînement**. Il sépare les contextes par équipement, rune, type de FM, tranche de puits, tranche de poids et **jet avant exact**. Il refuse les simulations et les sources non vérifiées.

Exécution : `python laboratoire_validation_predictive.py observations.csv --sortie validation.json --minimum 50`

La sortie indique couverture du test, score de Brier multiclasses, perte logarithmique et exclusions. Les scores restent absents si aucun groupe ne couvre les essais de test. `validation_suffisante` nécessite au moins 50 prédictions hors échantillon, mais **ne prouve pas** à elle seule une calibration suffisante.

**Aucun taux n'est injecté automatiquement dans les recommandations de l'overlay** : les taux exacts de DOFUS 3 ne sont pas connus et les données vérifiées doivent être collectées avant toute activation. Le laboratoire n'apparaît pas dans l'application.
