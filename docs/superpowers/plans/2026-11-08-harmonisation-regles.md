# Harmonisation FM — correction des incohérences auditées

Objectif autorisé : corriger les six points de l’audit, localement, sans perdre les données ni promettre des règles serveur inconnues.

1. Reproduire les divergences avec des tests : puits >100, parité des probabilités, gardes communes, refus explicite des malus non validés.
2. Une base de probabilités et de contraintes partagée. Conserver le modèle public Dofocus historique comme référence de régression séparée, jamais comme moteur actif. Versionner le nouveau modèle et garder les archives incompatibles sur disque.
3. Créer un modèle empirique figé à partir des seules transitions réelles complètes qualifiées, séparées par objet/rune/jet/puits/profil. Calibration commune (30 observations, a priori 200) et rééchantillonnage prudent des pertes constatées lorsqu’assez d’exemples du résultat existent. Aucun renforcement à partir des résultats simulés.
4. Raccorder ce modèle au conseiller, aux anticipations et à l’entraîneur. Sauvegarder l’instantané et son empreinte avec une politique ; audits reproductibles sans accès aux données actuelles.
5. Tests ciblés puis suite complète, revue indépendante finale et mise à jour de l’audit. Aucune publication GitHub ni suppression.

Décision : les coefficients déjà acceptés du modèle prédictif deviennent la référence commune provisoire, avec leurs hypothèses affichées. Les malus restent explicitement non simulables tant que les règles signées ne sont pas documentées et vérifiées ; aucune demi-densité supposée n’est conservée en moteur actif.

Décision : les 101 PWR restent des gardes conservatrices communes, déclarées comme choix logiciel. L’harmonisation ne transforme pas ces gardes en règles officielles.

Vérification : nouvelles reproductions rouges/vertes, snapshots exacts et rétractables, simulations jamais comptées comme réel, anciens modèles exclus sans effacement, comptabilité avant/après conservée à grande réserve de puits. Dossier de sauvegarde .test-tmp/harmonisation-backup-20261108.
