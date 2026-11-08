# Simulateur connecté au modèle du copilote

Autorisation : intégrer les nouvelles règles à l'entraîneur/simulateur du dépôt, puis mises à jour GitHub/locales cumulatives.

Approche : conserver l'API manuelle historique ; ajouter des sessions multi-lignes qui appellent le même classement et les mêmes prédictions à CHAQUE clic. Pas de nouveau moteur de probabilité. Respecter minima, plafonds, budget, prix et niveau.

Les pertes ne sont pas déterminées par SC/SN/EC. Par défaut : utiliser une transition réelle qualifiée du même état si disponible ; sinon absorber par le puits ou signaler transition inconnue. Option explicite `uniform` pour des pertes synthétiques, uniforme sur les lignes positives, aucune prétention de fidélité serveur. Compter le coût du clic même si la transition est inconnue. Afficher inconnues et bornes de réussite, ne pas présenter un taux tronqué comme probabilité en jeu. Les sorties virtuelles ne sont jamais des observations réelles et ne modifient pas la calibration.

- [x] Tests : SC conserve puits ; SN/EC pertes toutes lignes, excédent génère puits ; manque de puits n'est pas impossibilité ; données invalides bloquées.
- [x] Sessions : probabilités/Q/choix recalculés, arrêts objectifs/budget/limite, reproductibilité, invariants numériques.
- [x] Banque de pertes : lecture seule des transitions qualifiées, objet/rune/résultat/jet/puits exacts.
- [x] CLI : contexte JSON pour modèle dynamique, hypothèses manuelles conservées sous option explicite.
- [x] Interface : simulation de l'objectif courant, niveau et prix réels de référence, worker sans accès Tk, résultats signalés comme synthétiques.
- [x] Documentation, revue, suite complète, commit GitHub atomique et paquet cumulatif testé.

Ne pas annoncer un nouvel apprentissage RL ni une modification de Forgely-entrainement.exe absent des sources fournies.
