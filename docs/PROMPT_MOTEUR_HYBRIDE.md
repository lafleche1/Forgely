# Prompt — moteur hybride Forgely

Agis comme ingénieur logiciel senior et spécialiste des environnements de décision. Améliore le projet Forgely existant après inspection de son architecture ; réutilise ses moteurs, catalogues, bases et tests sans créer de doublons.

Implémente une architecture modulaire Python :

1. ItemState : état actuel, bornes naturelles, niveau, identité, puits et provenance/confiance du puits. Ne jamais transformer un puits inconnu en zéro certain.
2. TheoreticalEngine : adaptateur du moteur local DoFocus et du catalogue de poids existants. predict_outcome fournit une distribution SC/SN/EC ; la transition applique ensuite le résultat, les pertes et le puits. Distinguer règles documentées, modèle du simulateur et hypothèses. Ne jamais inventer une formule ou présenter DoFocus comme l’algorithme officiel du jeu.
3. EmpiricalCorrector : consulter en lecture seule les tentatives réelles confirmées et leur état avant. Apparier identité, rune, jet et puits ; lisser les fréquences vers le modèle théorique avec une force de prior configurable. Retourner le modèle inchangé sans données suffisantes. Exposer effectif, poids de correction et limites. Exclure observations ambiguës et simulations ; ne pas mélanger états incompatibles.
4. DecisionEnvironment : réutiliser ForgemagingEnv ; fournir actions, step, reset, graines reproductibles, budget, stock et horizon. Séparer actions admissibles des recommandations orientées objectif. Appliquer la distribution corrigée au tirage, puis réutiliser les transitions existantes. Récompense : progression vers le jet moins coût des runes ; toute estimation de profit doit disposer d’un modèle de prix explicite. Documenter la compatibilité et les écarts à Gymnasium.

Conserver les observations réelles et les simulations séparées avec provenance. Le mélange de conseils demandé est configurable, initialement 40 % simulation et 60 % réel ; il reste indépendant du lissage des probabilités. Les simulations ne calibrent jamais le correcteur empirique.

Avant un entraînement massif : tests de transitions, invariants et normalisation ; évaluation sur sessions réelles réservées, sans fuite entre entraînement et validation. Rapporter les scores de calibration et limites ; ne pas annoncer une amélioration sans mesure. Si aucune validation réelle indépendante n’est disponible, le dire explicitement.

Livrer le code intégré, les tests et leur résultat, un exemple reproductible, les limites et la documentation des paramètres. Préserver les interfaces existantes et ne pas modifier les données du joueur pendant les tests.
