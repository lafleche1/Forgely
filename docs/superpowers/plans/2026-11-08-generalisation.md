# Plan : politique généralisable, validation indépendante

Objectif autorisé : améliorer les décisions sur des états nouveaux et vérifier les gains, exclusivement localement.

Choix : conserver les probabilités et les contraintes du simulateur ; apprendre une politique compacte à partir de caractéristiques d'action (progression, déficit, masse, exposition et surplus), optimisée sur des trajectoires complètes. Une table d'états seule ne généralise pas ; multiplier ses sessions sans changer sa représentation n'est pas suffisant. Une recherche exhaustive à chaque conseil serait coûteuse ; une politique compacte peut être évaluée en mémoire.

- Mesurer les politiques candidates sur des graines d'apprentissage séparées, sans consulter l'audit final.
- Tests avant implémentation : état inédit, invariance au prix, actions légales, cible simultanée, reprise, chargement et validation.
- Implémenter le candidat retenu avec budget borné, annulation et archives compatibles explicites.
- Comparer au témoin et à l'ancienne politique ; figer le candidat avant un audit final de 1 000 sessions sur une nouvelle graine.
- N'activer que si les critères conservateurs existants sont satisfaits. Le résultat en jeu demeure non démontré sans observations réelles suffisantes.
- Exécuter tests, relecture, reconstruire l'entraîneur et livrer rapport mesuré.


Décisions pendant l'exécution :
- Le tournoi apprend parmi huit fonctions compactes et la table, à budget borné.
  Les paramètres sont choisis sur des trajectoires de formation, dont des
  départs difficiles identiques entre candidats. Les essais finaux restent séparés.
- La table a atteint 50 000 états sur la campagne étendue : la nouvelle fonction
  de décision continue de produire des scores sur des états inédits.
- Les observations réelles disponibles sont insuffisantes : aucune calibration
  du modèle n'est ajoutée et aucun résultat simulé ne devient une observation.
- La relecture a identifié une différence entre politique directe et sélecteur
  du copilote. Un garde exige maintenant un audit de ce sélecteur lié à
  l'empreinte des paramètres avant d'autoriser une politique généralisable.
  Aucun résultat d'entraînement ne suffit à lui seul à cette autorisation.

- Décision après audit : 834/1000 contre 860/1000 au témoin et 840/1000 pour
  l'ancienne politique. La piste n'est pas promue. Elle devient une option
  explicitement expérimentale, décochée par défaut ; ce changement ne modifie
  ni le candidat figé ni les résultats de l'audit. Les protections restent actives.
