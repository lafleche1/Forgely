# Modèle vidéo et calibration — Implementation Plan

Objectif autorisé : modèle vidéo prioritaire, calibré par les résultats réels comparables ; préserver puits, objectifs et budget.

Choix : module Python pur séparé. Formule finale pour SC ; SN approximatif reconstruit avec la règle par morceaux du premier écran, explicitement identifié. Q suit la précision utilisateur : moyenne des ratios de toutes les lignes naturelles, borné à [0,1] ; exo PA/PM/PO existant impose Q=1 sans second +60. Niveau inconnu : aucun bonus, signalé. Profils manquants : repli existant. Exos lourds : référence communautaire séparée, sans plancher 2 %. Aucun taux de perte de PA universel ajouté.

Calibration : comptages exacts objet/rune/jet/puits, uniquement nouvelles transitions dont toutes les lignes naturelles documentées sont présentes et comptabilité cohérente. Aucune promotion rétroactive des OCR partiels. Prior de 200 essais, seuil 30 essais réels ; fréquences brutes séparées et poids réel affiché. Pas de données simulées dans les comptages.

- [x] Tests numériques : seuils 80 %, ×14, over, Q, niveau, exos, données manquantes et taux normalisés.
- [x] Module forgely_predictive.py : estimate et calibrate, contexte et hypothèses explicites.
- [x] Décision : pondérer progression et exposition par SC/SN/EC ; prix inchangés ; afficher taux et alternatives.
- [x] Contexte/laboratoire : certification conservatrice, comptages exacts persistants ; interface active raccordée.
- [x] Documentation, comparaison avant/après sans prétendre mesurer la performance en jeu ; suite complète et compilation.
