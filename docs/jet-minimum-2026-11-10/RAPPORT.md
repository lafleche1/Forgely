# Jet souhaité : seuils minimums

Modification appliquée le 10 novembre 2026 dans le projet local Forgely v22.16.

## Règle

Une caractéristique est satisfaite dès que `actuel >= T`. Son manque est `max(0, T - actuel)`. Le surplus ne reçoit ni pénalité de cible ni progression supplémentaire. Aucune rune ne vise à réduire une ligne déjà satisfaite. Les restrictions indépendantes de maximum naturel, d'over demandé, d'exo et de densité de ligne restent contrôlées.

## Changements

- Suppression de la pénalité de dépassement dans le classement du moteur et les politiques générales, y compris celles enregistrées avec un ancien paramètre de pénalité.
- Les cibles explicites d'over/exo ne plafonnent plus le gain autorisé ; les contrôles physiques restent appliqués.
- Les chemins de finition et les plans de remontée acceptent une finition supérieure au minimum. Le planificateur mesure uniquement le manque réparé, sans compter le surplus comme un progrès supplémentaire.
- Le simulateur d'une ligne accepte un jet déjà satisfaisant et retourne une réussite sans tentative.
- L'entraîneur accepte les jets initiaux déjà satisfaisants et partage l'exception existante du moteur pour une finition par la plus petite rune indivisible. Les plus gros overs non demandés restent exclus.
- Les tableaux, éditeurs et l'entraîneur présentent clairement les objectifs comme des minimums.
- Les nouvelles régressions couvrent satisfaction, manque, affichage, classement, récompense, finition, contraintes d'over et malus. Les couches de progression déjà conformes ont été vérifiées sans réécriture inutile.
- L'empreinte de validation des politiques inclut désormais les deux planificateurs de finition/remontée modifiés.

## Fichiers modifiés

Application (12 fichiers) :

- `Application/forgely_decision.py`
- `Application/forgely_general_policy.py`
- `Application/forgely_finish_paths.py`
- `Application/forgely_pool_repair.py`
- `Application/forgely_rl.py`
- `Application/forgely_simulateur.py`
- `Application/forgely_training.py`
- `Application/forgely_live_targets.py`
- `Application/forgely_equipment_picker.py`
- `Application/forgely_dashboard.py`
- `Application/forgely_overlay.py`
- `Application/entrainer_forgely.py`

Tests (5 fichiers) :

- `Tests/test_minimum_targets.py` : nouveau, 20 cas.
- `Tests/test_pa_finish_sequences.py`
- `Tests/test_training_regressions.py`
- `Tests/test_sequence_planning.py`
- `Tests/test_audit_corrections.py`

## Vérification finale

Suite complète : **2 313 tests réussis, 31 ignorés, 42 sous-tests réussis, aucun échec**. Durée : 166,59 secondes. Code de sortie : 0.

Commande : `.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp=.test-tmp/jet-minimum-verified`.

Pour cette exécution seulement, `TEMP` et `TMP` pointaient vers `.test-tmp/jet-minimum-env` et le dossier déjà installé `C:\Program Files\Tesseract-OCR` était ajouté au chemin des programmes. Aucune installation ni modification permanente de l'environnement.

Le journal définitif est `pytest-verified.log`. Les journaux antérieurs conservent les reproductions initiales et les attentes de tests corrigées ; ils ne représentent pas le résultat final. Les tests ignorés n'ont pas été validés par cette exécution.

## Préservation du travail local

Aucun dépôt Git n'était présent dans ce dossier. Les modifications sont des retouches ciblées des fichiers locaux existants, sans réinitialisation ni remplacement par une autre version. Les versions avant modification sont conservées sous `before/` ; `changes.diff` contient les différences et les nouveaux tests. Les autres fichiers du projet n'ont pas été réécrits.
