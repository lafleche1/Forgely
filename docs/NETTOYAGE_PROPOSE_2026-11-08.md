# Nettoyage effectué localement — 8 novembre 2026

Les sept dossiers ci-dessous ont été supprimés après autorisation explicite du joueur.
Aucune modification n'a été envoyée à GitHub pour ce nettoyage.
Les tailles sont celles de l'inventaire du 8 novembre, arrondies en Mio.

| Dossier dans Forgely | Taille | Pourquoi le proposer |
|---|---:|---|
| `distribution/restauration-20261108-121130-2d888f` | 55,29 Mio | Archive assemblée d'une ancienne restauration ; la distribution 22.15 et la sauvegarde avant fusion sont conservées. |
| `distribution/restauration-20261108-132113-ceb139` | 55,39 Mio | Archive assemblée identique à celle du dossier de 15 h 06 ; son SHA-256 correspond à la distribution conservée dans les morceaux. |
| `distribution/restauration-20261108-150650-9829b5` | 55,39 Mio | Deuxième exemplaire de la même archive 22.15, reconstructible à partir de `distribution/parts`. |
| `Forgely-complet-20261108-150650-9829b5` | 36,39 Mio | Copie extraite de l'ancienne restauration ; le dossier principal mis à jour devient la version à lancer. À enlever seulement après validation de son lancement par le joueur. |
| `.test-tmp/distribution-check` | 88,53 Mio | Copie de contrôle extraite pour vérifier l'ancienne distribution, sans rôle dans le lancement. |
| `.test-tmp/distribution-final-check` | 88,70 Mio | Deuxième extraction de contrôle de l'ancienne distribution. |
| `.pytest_cache` | 0,15 Mio | Cache des tests, recréé automatiquement ; aucune donnée du joueur. |

Gain envisagé : environ **380 Mio**. Avant une suppression autorisée, les chemins
absolus seront revérifiés et la présence des sources, sauvegardes et morceaux
de distribution à conserver sera contrôlée.

## À conserver

- `Application`, `Tests`, `docs`, `outils`, les lanceurs et `.venv` : application,
  contrôles et environnement nécessaire au lancement.
- `Entrainements` et `Entrainement_Forgely.exe` : historiques simulés et entraîneur.
- `distribution/parts`, son manifeste et le programme de restauration : archive
  de secours 22.15 conservée, distincte des nouvelles sources 22.16.
- `.test-tmp/fusion-backup-20261108` : sauvegarde avant fusion et inventaire SHA-256.
- `.test-tmp/fusion-github` : copie Git de travail de la fusion et de sa publication.
- `.test-tmp/fusion-clean-check` et les journaux `fusion-*` : preuve de validation
  de cette mise à jour ; réexamen possible après utilisation de la nouvelle version.

Ne pas supprimer `.test-tmp` en bloc : il contient aussi ces éléments à conserver.

## Résultat vérifié

7 dossiers supprimés ; 398 300 446 octets libérés, soit 379,85 Mio.
Les empreintes de 3 509 fichiers conservés de l’application, des entraînements
et de la distribution sont inchangées. Les sauvegardes de fusion et le dossier
Git de travail ont été conservés.
