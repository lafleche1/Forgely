# Intégration du moteur local

Objectif : calculer et tester les runes hors ligne selon les mécanismes Dofocus identifiés, puis croiser ces simulations avec les observations réelles de Forgely.

1. Produire des cas de référence numériques en exécutant le noyau public déjà analysé dans un contexte isolé. Couvrir naturel, over, exo, malus, niveaux, plafonds, puits et pertes avec des suites aléatoires déterministes. Ne pas distribuer le JavaScript tiers.
2. Écrire puis vérifier une implémentation Python indépendante des calculs et transitions. Valider les entrées et garder la provenance du modèle ; ne jamais présenter ses chances comme des probabilités officielles du jeu.
3. Préparer les états à partir du catalogue complet, calculer les chances immédiatement et exécuter les essais virtuels dans un worker dédié. Cache borné, dernière demande prioritaire, résultats liés au jet/puits/cibles exacts, aucune écriture dans les observations.
4. Raccorder le classement et l'explication au moteur local, en conservant les contrôles de budget, de profil et de lecture. Les données des joueurs restent distinctes et calibrent les contextes comparables. Vérifier parité, intégration, isolation et performances, puis faire relire les changements.

## Résultat et validation

- Implémentation Python indépendante, sans JavaScript distant en production ; 359 cas de chances et 1 077 transitions déterministes comparés au noyau public.
- 48 essais virtuels par rune en arrière-plan ; attente de résultat et accès SQLite exclus du thread Tk. Les plafonds locaux ne peuvent pas être annulés par un ancien relevé enregistré.
- Statistiques virtuelles persistées séparément à la demande de l'utilisateur ; compteurs réel/simulé/total, déduplication des mêmes essais déterministes, aucune insertion des simulations dans les observations réelles.
- Référentiel régénéré depuis l'installation DOFUS : 19 569 lignes naturelles, avec correction des résistances en pourcentage de catégorie 1 qui étaient omises.
- Relecture indépendante : attente SQLite dans l'interface corrigée avec cache alimenté en arrière-plan ; valeurs hors domaine rejetées avant le calcul immédiat.
- Suite finale : 1 270 tests réussis, 24 ignorés, 42 sous-tests réussis. Parcours natifs ciblés également vérifiés.
- Microbenchmark local Anneau du Cycloïde : initialisation du contexte 89,88 ms ; calcul d'une rune 0,0217 ms en moyenne ; environ 32 417 tentatives isolées par seconde. Ce n'est ni la vitesse d'un entraînement RL complet, ni la latence capture/OCR/conseil.
- Les fonctions pures `odds` et `attempt` peuvent servir à un environnement RL ; aucun entraînement RL massif n'a été lancé pendant cette intégration.
