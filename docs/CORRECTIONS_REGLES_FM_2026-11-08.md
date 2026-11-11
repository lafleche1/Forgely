# Correction des incohérences FM — livraison locale du 8 novembre 2026

## Corrections réalisées

1. **Puits sans plafond artificiel de 100.** Un EC de poids 1 avec une réserve de 180 laisse 179 si aucune caractéristique ne tombe ; un SC conserve 180. La comptabilité d’observation et les essais virtuels ne se contredisent plus sur ce point.
2. **Une base commune pour SC/SN/EC.** Conseiller, simulateur et entraîneur utilisent `forgely-unified-fm-2026-11-08-v1`. La référence provisoire des exos lourds est 1 % partout avant calibration, avec l’étiquette communautaire/non officielle. Q, seuils et règles de taille sont partagés. Les références Dofocus historiques restent descriptives et les anciennes parités sont conservées dans un module de recherche non actif.
3. **Tri et affichage cohérents.** Les phases de puits conservent leurs préférences et leur repli, mais ne passent plus par des fourchettes fixes concurrentes. Elles utilisent SC+SN du modèle partagé. Le niveau connu de l’objet et la calibration exacte du contexte sont repris dans l’explication.
4. **Gardes communes.** Fin de la garde supplémentaire sur la masse cumulée des overs du simulateur. Les mêmes gardes conservatrices sont utilisées par les chemins actifs. Elles restent des choix du logiciel, pas des règles serveur certifiées.
5. **Malus traités honnêtement.** Suppression de l’utilisation active d’une demi-densité supposée. Les profils signés non validés sont refusés explicitement par le simulateur et l’entraîneur, et signalés par le conseiller. La correction empêche des résultats trompeurs ; elle ne prétend pas avoir appris toutes les règles des malus.
6. **Vidéos raccordées à l’entraînement et aux anticipations.** Les observations complètes qualifiées peuvent corriger les probabilités et fournir des états après/pertes effectivement observés. Seuil de 30 comparables, a priori 200 ; au moins 5 exemples du résultat pour rééchantillonner ses pertes. Correspondance exacte objet/rune/jet/puits/bornes/poids. Aucun état simulé n’est ajouté aux observations réelles.
7. **Instantanés par objet.** Les entraînements utilisant le réel conservent leur jeu de données et son empreinte. Un audit ne remplace pas ce jeu par la base actuelle. Les tirages sont identiques après sauvegarde/rechargement. Des données ajoutées sur un autre objet ne changent pas inutilement la révision de son modèle.
8. **Pas de double comptage.** Un posterior déjà calibré n’est pas recalibré ni ajusté une seconde fois par les mêmes observations. Les explications et la trace reflètent cette règle.
9. **Anciennes politiques conservées et isolées.** Nouvelle version de modèle, signatures de données et audit du sélecteur empêchent leur réutilisation silencieuse dans un autre contexte. Les archives d’entraînement ne sont pas supprimées. Les sources live non figées ne peuvent pas activer une influence apprise hors du domaine audité.

## Vérification

- Suite finale de cette conversation : **1 727 tests réussis, 25 ignorés, 42 sous-tests réussis**, zéro échec, 74,52 secondes. Journal `.test-tmp/harmonisation-full-05.log`.
- Revue indépendante finale : aucun défaut important confirmé restant ; 53 tests ciblés passés. Le problème de déterminisme des pertes à la restauration a été reproduit par un test hétérogène rouge puis corrigé.
- Vérifications de la chaîne empirique : qualification/rejet, exclusion des données simulées ou non certifiées, rétraction, séparation des objets/puits, calibration unique, pertes observées, reprise avec un autre état de la base et audit de l’instantané d’origine.
- Interface de l’entraîneur vérifiée à 1020×700 et 860×620, y compris le formulaire de revue. Lanceur natif existant testé sur les sources actuelles : code de sortie 0.
- Compilation Python réussie.
- Contrôle d’intégrité : 17 fichiers de production inventoriés ; empreintes vérifiées après les tests. Les 105 poids/gains de rune restent documentés.

Empreinte finale du sélecteur : `65dd609771edaf0b938fbb51623d870a388afc72ed2ef499e69b45d53e99097e`.

L’autre conversation a achevé ses vérifications coordonnées sur cette même empreinte : 1 730 tests réussis, 26 ignorés, 42 sous-tests. Ces nombres viennent d’un lancement séparé et ne sont pas additionnés aux précédents. Son audit pertinent utilise le profil Windows réel : `docs/audit-corrections-2026-11-08/selector-user-runtime-audit.json`, contrôle borné de 50 épisodes par bras, 16 succès par bras et aucune activation. Les anciens audits d’une autre empreinte sont explicitement périmés.

Cet audit ne démontre pas une amélioration du taux de réussite en jeu. Les statistiques de tests logiciels ne sont pas des taux de réussite de forgemagie.

## Utilisation et portée

Le lanceur source local `Entrainement_Forgely.exe` ouvre ces changements. Dans Sessions virtuelles, « Utiliser les observations réelles fiables » est activé par défaut ; une base sans observations qualifiées conserve le modèle provisoire. Les overs préparatoires restent un mode de comparaison expérimental.

Les fichiers principaux antérieurs sont sauvegardés dans `.test-tmp/harmonisation-backup-20261108`. L’API historique de classification a été préservée dans `forgely_fm_classification.py` et reste réexportée. Les ajouts parallèles du sélecteur, des prix, des objectifs mesurés et de séparation de l’historique ont été conservés.

**Aucun nouveau commit ni push GitHub depuis ce correctif.** Les archives distribuées n’ont pas été remplacées. Les règles serveur non vérifiées, les pertes sans données suffisantes et les malus restent des limites déclarées.

## Détail vérifiable

- [Règles actuellement appliquées](REGLES_FM_HARMONISEES_2026-11-08.md)
- [Inventaire, versions, empreintes et preuves numériques](HARMONISATION_FM_2026-11-08.json)
- [Audit antérieur conservé comme historique](REGLES_REELLEMENT_UTILISEES_2026-11-08.md)
