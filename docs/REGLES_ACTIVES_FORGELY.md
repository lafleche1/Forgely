# Les règles réellement appliquées par Forgely

Mise à jour 22.16 : le budget avertit par défaut et ne suspend les conseils que
si l'option est activée. Le modèle vidéo estimé, sa calibration sur transitions
qualifiées et les bilans coexistent avec la matrice et l'apprentissage PC.
Voir [la synthèse courante et les choix de fusion](FUSION_PC_GITHUB_2026-11-08.md).

RÈGLES ACTIVES DU COPILOTE — 8 novembre 2026
1. Atteindre tous les minima du jet demandé. Ne pas remplacer ces cibles par un jet parfait ou une valeur de revente.
2. Conseiller uniquement sur un objet et un jet confirmés, avec toutes les lignes ciblées présentes et un puits confirmé. Après une pose, attendre la nouvelle lecture.
3. Ne jamais déduire le puits des points manquants au jet parfait. Le puits n’est pas plafonné à 101.
4. SC : puits conservé. SN/EC : max(0 ; puits initial + poids des pertes − poids de la rune). Les pertes du jet complet doivent être connues pour certifier le calcul.
5. Poids = gain de la rune × poids par point, distinct du poids d’inventaire. Un seul référentiel versionné est partagé entre les moteurs.
6. Bornes naturelles documentées : dépassement = over ; absence = exo uniquement si le profil naturel est complet. Un CSV partiel ne prouve pas une absence.
7. Gardes conservatrices : densité totale d’une ligne over ≤101, sauf maximum naturel supérieur ; densité cumulée des lignes exotiques ≤101. Ce sont des gardes de Forgely, pas une formule officielle reconstituée.
8. Exo possible sans puits. Aucun sacrifice automatique et aucun ordre universel de quatre phases. Remonter une ligne naturelle ciblée disponible avant une finition over/exo.
9. Minima atteints : arrêt. Aucun budget dur ne bloque les conseils. Aucun seuil automatique à 98 % du jet parfait et aucun seuil de risque fictif à 60 %.
10. Chances maximales : progression, équilibre, palier simple/Pa/Ra et exposition. Budget optimisé : scores positifs de progression divisés par (1 + prix unitaire). Aucun coût final minimal garanti.
11. Prix absents : classement économique suspendu pour les candidats concernés ; un prix inconnu ne signifie jamais gratuit.
12. Scénario SC : gain nominal, puits conservé, prix déduit du budget, puis nouveau conseil hypothétique. SN/EC : relire les pertes avant de choisir la prochaine rune.
13. Risque qualitatif : Faible si rune couverte ; Moyen si poids non couvert ; Critique pour finition ou over/exo déjà présent et identifié. Ce ne sont pas des probabilités. Un profil partiel peut laisser une fragilité inconnue.
14. Aucun pourcentage de confiance ou de réussite finale inventé. Aucun coefficient de difficulté serveur déduit d’une série d’échecs.
15. Relevés Dofocus : réutilisation seulement pour le même objet, jet complet et puits exacts. Leur SC+SN affiché peut pondérer le classement ; cela ne valide pas ces chiffres comme probabilités du jeu.
16. Observations réelles agrégées : descriptives. Statistiques OCR contextuelles à partir de 30 échantillons, par objet, rune, jet exact et classe de puits, avec intervalle SC ; elles restent exploratoires et ne recalibrent pas le classement.
17. Simulations et observations restent séparées. Les politiques apprises restent inactives sans validation indépendante. Le mélange 60 % réel / 40 % simulations exige les validations et le contexte requis.
18. Malus non traités par les règles positives ; transcendances, chasse et Signature ne sont pas proposées comme runes ordinaires. Mode observation : aucun conseil. Aucun clic automatique dans DOFUS.
19. Bilans de sessions : objectifs/coûts locaux, prévisions antérieures au résultat comparées uniquement sur contexte identique et transition cohérente. Les bilans ne créent aucune observation supplémentaire. Les nouvelles transitions qualifiées enrichissent la calibration ; amélioration progressive, non garantie à chaque session.

PRIX : Tylezia ; référence reçue le 2026-11-08 ; valeurs modifiables, non actualisées automatiquement.

PROVENANCE DES POIDS : Données du client Ankama extraites par un tiers ; pas une publication ou validation officielle Ankama. Les densités ne sont ni des probabilités ni les poids d’inventaire.
Client 3.7.13.17 ; extraction : https://github.com/ledouxm/dofus-sqlite/releases/tag/v6.0_3.7.13.17


La table détaillée est dans [POIDS_RUNES.md](POIDS_RUNES.md).
