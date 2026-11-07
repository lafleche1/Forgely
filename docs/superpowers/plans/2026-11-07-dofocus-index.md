# Référentiel Dofocus léger — plan

Objectif : préparer une croissance des références sans lecture complète du catalogue ni scan linéaire pendant les conseils. L'utilisateur délègue les choix et autorise l'exécution autonome.

Choix : SQLite en lecture seule, bibliothèque standard Python. Un index mémoire global aurait chargé tous les relevés ; des fichiers JSON par objet auraient multiplié les fichiers et nécessité un catalogue de routage. SQLite fournit une recherche par clé et un cache borné, sans nouvelle dépendance. Les poids communs restent disponibles même sans relevé exact.

Contraintes : jamais d'extrapolation de taux, ni de données simulées dans les observations ; conserver les deux objectifs et le budget ; aucune requête réseau pour conseiller ; ne pas réécrire le modèle Dofocus non publié.

- [x] Tests RED pour la construction validée et atomique, la lecture exacte sans JSON complet, les nombres équivalents, les erreurs et la taille bornée du cache.
- [x] Construire une base indexée depuis le JSON d'auteur, déplacé hors des ressources de l'exécutable. Valider uniquement les données demandées à la lecture, conserver l'identité et le contexte complet.
- [x] Brancher le moteur sur un contexte préparé une fois par décision. Tests GREEN et suite complète.
- [x] Produire une liste bornée de situations à relever, avec priorité et motif ; cibles de collecte uniquement, sans probabilités inventées. Prioriser les familles/régimes peu couverts et dédupliquer les états déjà connus.
- [x] Mesurer l'ancien et le nouveau moteur sur la base réelle et une fixture synthétique de 3 000 contextes ; publier taille, latence et limites, sans confondre cette fixture avec des données Dofocus.
- [x] Vérifier packaging et revue indépendante ; préparer la validation CI et la publication.

Fichiers : forgely_dofocus.py garde règles et validation ; forgely_dofocus_store.py gère le stockage ; preparer_reference_dofocus.py construit la ressource SQLite ; preparer_collecte_dofocus.py produit les cibles ; assets/dofocus/reference.sqlite3 est la ressource runtime ; references/dofocus/reference.json est la source auditable. Tests dans test_dofocus_store.py et test_dofocus_collection.py.

Revue : référence absente/corrompue, cache borné et invalidation, JSON non chargé par l'interface, égalité numérique exacte, aucune contamination d'observations. La collecte n'est pas lancée en masse ; les cibles préparent des vérifications utiles et n'inventent pas leur résultat.

## Résultats

- Base avant changement : 356 tests réussis, 15 ignorés, 25 sous-tests.
- Cycle RED/GREEN : stockage exact, cache borné, lecture sans JSON d'auteur, erreurs et construction atomique ; collecte bornée sans résultats inventés.
- Suite : 367 tests réussis, 15 ignorés (9 GUI locaux, 6 captures absentes), 25 sous-tests ; contrôle GUI prévu sur CI.
- Revue indépendante : aucun problème actionnable relevé ; 28 tests ciblés et 6 sous-tests réussis.
- Base runtime 77 824 octets ; cache 32 objets et 64 contextes. Le JSON d'auteur reste auditable hors ressources runtime.
- Décision : règles communes inchangées, pas de reconstruction de la formule ni de collecte exhaustive. Le plan de 64 entrées est explicitement non collecté.
- Mesures détaillées dans docs/PERFORMANCES_REFERENCE_V22_03.md. La fixture 3 000 contextes est fictive et supprimée après mesure ; aucune tentative ajoutée.
- Publication : contrôle de la branche distante et validation CI avant déplacement de main.


## Intégration OCR concurrente

Main a reçu 1764a8b (optimisations OCR v22.02) pendant cette préparation. Ces 17 fichiers ont été récupérés ; le seul chevauchement du code principal était notre changement de numéro de version. Les fichiers d'OCR et leurs tests sont conservés. La version combinée devient v22.03. Les mesures de ce rapport concernent uniquement la référence ; les mesures OCR restent documentées séparément dans docs/PERFORMANCE_OCR.md.


Validation après intégration OCR : 411 tests réussis, 15 ignorés et 25 sous-tests ; 153 fichiers Python compilés. Le premier passage avait signalé MSS absent de l'environnement local ; la dépendance déjà déclarée dans requirements a été installée, puis la suite entière relancée avec succès. Aucun correctif produit n'a été nécessaire pour cette absence locale.
