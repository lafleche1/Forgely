# Les règles réellement appliquées par Forgely

RÈGLES ACTIVES DU COPILOTE — 8 novembre 2026
1. Atteindre tous les minima du jet demandé. Ne pas remplacer ces cibles par un jet parfait ou une valeur de revente.
2. Conseiller uniquement sur un objet et un jet confirmés, avec toutes les lignes ciblées présentes et un puits confirmé. Après une pose, attendre la nouvelle lecture.
3. Ne jamais déduire le puits des points manquants au jet parfait. Le puits n’est pas plafonné à 101.
4. SC : puits conservé. SN/EC : max(0 ; puits initial + poids des pertes − poids de la rune). Les pertes du jet complet doivent être connues pour certifier le calcul.
5. Poids = gain de la rune × poids par point, distinct du poids d’inventaire. Un seul référentiel versionné est partagé entre les moteurs.
6. Bornes naturelles documentées : dépassement = over ; absence = exo uniquement si le profil naturel est complet. Un CSV partiel ne prouve pas une absence.
7. Gardes conservatrices : densité totale d’une ligne over ≤101, sauf maximum naturel supérieur ; densité cumulée des lignes exotiques ≤101. Ce sont des gardes de Forgely, pas une formule officielle reconstituée.
8. Exo possible sans puits. Aucun sacrifice automatique et aucun ordre universel de quatre phases. Remonter une ligne naturelle ciblée disponible avant une finition over/exo.
9. Minima atteints : arrêt. Budget restant nul : arrêt. Aucun seuil automatique à 98 % du jet parfait et aucun seuil de risque fictif à 60 %.
10. Modèle vidéo prioritaire : seuil 80 %, pression dès ×14, over et qualité globale. Chances maximales : progression pondérée par SC+SN estimés. Budget optimisé : prix et exposition de réparation approximative. Aucun coût final minimal garanti.
11. Prix absents : runes exclues du mode économique et des conseils sous budget. Budget 0 dans les préférences = sans limite ; dépenses inconnues = conseil sous budget suspendu.
12. Scénario SC : gain nominal, puits conservé, prix déduit du budget, puis nouveau conseil hypothétique. SN/EC : relire les pertes avant de choisir la prochaine rune.
13. Risque qualitatif : Faible si rune couverte ; Moyen si poids non couvert ; Critique pour finition ou over/exo déjà présent et identifié. Ce ne sont pas des probabilités. Un profil partiel peut laisser une fragilité inconnue.
14. Aucun pourcentage de confiance ou de réussite finale inventé. Aucun coefficient de difficulté serveur déduit d’une série d’échecs.
15. Formule finale vidéo pour SC ; Q = moyenne des ratios actuels/maxima naturels par ligne, bornée à [0,1] selon la définition utilisateur. Exo PA/PM/PO existant : Q=1 sans second +60. SN reconstruit par morceaux ; ces hypothèses sont affichées. Niveau optionnel 1–200 dans les objectifs ; inconnu : aucun bonus. Les relevés Dofocus exacts restent séparés et servent de repli si le modèle manque.
16. Calibration : après 30 essais réels comparables, moyenne avec un prior de 200 essais du modèle. Même objet, rune, jet exact et puits exact ; toutes les lignes naturelles documentées présentes et comptabilité cohérente. Les anciens OCR partiels et simulations ne calibrent jamais. Les fréquences agrégées restent descriptives.
17. Simulateur dynamique : même modèle après chaque clic, minima/prix/budget respectés ; pertes réelles comparables ou transition inconnue, approximation explicite facultative. Les essais virtuels restent séparés des observations. Aucun RL, MCTS, A* ou mélange 40/60 implicite.
18. Malus non traités par les règles positives ; transcendances, chasse et Signature ne sont pas proposées comme runes ordinaires. Mode observation : aucun conseil. Aucun clic automatique dans DOFUS.
19. Bilans de sessions : objectifs/coûts locaux, prévisions antérieures au résultat comparées uniquement sur contexte identique et transition cohérente. Les bilans ne créent aucune observation supplémentaire. Les nouvelles transitions qualifiées enrichissent la calibration ; amélioration progressive, non garantie à chaque session.

PRIX : Tylezia ; référence reçue le 2026-11-08 ; valeurs modifiables, non actualisées automatiquement.

PROVENANCE DES POIDS : Données du client Ankama extraites par un tiers ; pas une publication ou validation officielle Ankama. Les densités ne sont ni des probabilités ni les poids d’inventaire.
Client 3.7.13.17 ; extraction : https://github.com/ledouxm/dofus-sqlite/releases/tag/v6.0_3.7.13.17


Modèle : [MODELE_VIDEO_CALIBRATION.md](MODELE_VIDEO_CALIBRATION.md).
Bilans : [BILAN_SESSIONS_APPRENTISSAGE.md](BILAN_SESSIONS_APPRENTISSAGE.md).
Simulateur : [SIMULATEUR_DYNAMIQUE.md](SIMULATEUR_DYNAMIQUE.md).
Pertes : [RECHERCHE_PERTES_FM.md](RECHERCHE_PERTES_FM.md).
Poids : [POIDS_RUNES.md](POIDS_RUNES.md).
