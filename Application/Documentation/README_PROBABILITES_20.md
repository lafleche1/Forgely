# Forgely 0.20 — Calculs vérifiables et probabilités conditionnelles

Le laboratoire externe `laboratoire_probabilites.py` regroupe **uniquement** les tentatives réelles explicitement vérifiées, selon équipement, rune, type de FM, classe de puits et classe de poids. Les résultats sont des fréquences SC/SN/EC avec intervalles de Wilson à 95 %, **pas les probabilités officielles du jeu**. Minimum 50 observations par groupe par défaut. Les simulations, lectures automatiques non confirmées et données incomplètes sont rejetées. L'application ne change pas de recommandation sur la base d'une petite série.

Commande : `python laboratoire_probabilites.py observations.csv --sortie rapport.json --minimum 50`

Colonnes CSV : `date_utc,equipement,rune,resultat,source,jet_avant,puits_avant,type_fm,poids_rune`. Sources autorisées : `manual`, `ocr_confirmed`, `video_verified`. Types : `fm_classique`, `over`, `exo`. Le champ `jet_avant` est obligatoire, mais **pas encore interprété** pour stratifier par qualité de jet : des situations différentes peuvent rester regroupées. Une source étiquetée vérifiée doit l'être réellement par le collecteur; le laboratoire ne peut pas authentifier une déclaration CSV. Les bornes des classes de puits et de poids sont des choix analytiques, pas des lois de DOFUS.

Les règles documentaires, poids de rune, plafond supplémentaire communautaire et gestion du reliquat restent dans `forgely_probabilites.py`, `forgely_decision.py` et `forgely_connaissances.py`. Aucune affirmation issue d'une vidéo dont les gestes n'ont pas été relevés ne devient une constante de probabilité. L'estimateur reste externe tant que sa validation sur des observations indépendantes n'est pas suffisante.
