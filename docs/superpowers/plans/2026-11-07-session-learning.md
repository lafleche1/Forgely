# Apprentissage des sessions

Objectif : relier les transitions persistantes au classement des conseils sans contourner les règles ni le budget.

Choix : conserver SQLite et le laboratoire existants ; exclure un modèle distant ou un réentraînement lourd. Adaptation locale limitée à ±20 %, seuil de 30 transitions cohérentes, même objet/rune/jet et classe de puits. Données OCR cohérentes mais non certifiées. Voir docs/APPRENTISSAGE_LOCAL.md pour les limites.

- [x] Tester l'absence initiale de connexion entre historique et classement.
- [x] Ajouter le filtrage avant/après dans forgely_labo_live.py.
- [x] Ajouter learning_for et un ajustement borné dans forgely_decision.py.
- [x] Connecter strategy_current au laboratoire.
- [x] Vérifier seuil, persistance, rejets et budget ; exécuter toute la suite.
