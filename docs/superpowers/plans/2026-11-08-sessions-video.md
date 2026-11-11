# Sessions vidéo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Importer et analyser les MP4 dans l’entraîneur et transmettre des observations traçables à Forgely.

**Architecture:** Module de stockage/revue vidéo, analyseur visuel indépendant de Tk, panneau intégré à l’entraîneur. Calibration partagée par lecture d’une table vidéo distincte, sans modifier les captures écran existantes.

**Tech Stack:** Python, Tkinter, OpenCV, Pillow, OCR Tesseract existant, SQLite.

**Spec:** docs/superpowers/specs/2026-11-08-sessions-video-design.md

## Global Constraints

- Aucun traitement audio.
- Développement local ; vidéos originales et apprentissages existants conservés.
- Observations par objet et contexte complet ; simulations séparées.
- Aucune amélioration en jeu annoncée sans mesure réelle.

## Review Focus

- Même vidéo déplacée ou réimportée : aucune observation doublée.
- Coupe, plusieurs événements entre lectures, changement d’objet : pas de faux appariement.
- Puits inconnu et lignes masquées : aucune conversion en zéro.
- Correction/rejet après transmission : recalcul remplaçant la contribution précédente.
- Annulation/fermeture de fenêtre : sauvegarde, reprise et absence d’appel Tk depuis un travailleur.

### Task 1 — Stockage et qualification

Files: Application/forgely_video_store.py, Tests/test_video_store.py.
Interfaces: VideoStore(directory), save_session/load_session, qualify_event, transfer_session(session, db_file), qualified_video_rows(db_file).
- [ ] Écrire puis exécuter des tests rouges : SC conserve le puits, profil incomplet interdit, puits inconnu interdit, import idempotent, correction/rejet rétractent les anciennes contributions.
- [ ] Implémenter stockage JSON atomique, historique, preuve et table SQLite vidéo distincte.
- [ ] Exécuter les tests et vérifier le résultat vert.

### Task 2 — Analyse visuelle MP4

Files: Application/forgely_video_analysis.py, Tests/test_video_analysis.py.
Interfaces: video_info, frame_at, VisualReader(zones), analyze_video(path, store, zones, cancel, progress, reader=None).
- [ ] Tests rouges pour décodage MP4 synthétique, validation des zones, événements stables sans double compte, multi-événements et coupe, reprise/annulation.
- [ ] Décodage local, échantillonnage adaptatif, OCR zones, reconnaissance catalogue/runes, appariement stable conservateur ; persister images de preuve et état de reprise.
- [ ] Tests verts ; aucun échantillon simulé transmis comme observation réelle.

### Task 3 — Interface intégrée

Files: Application/forgely_video_ui.py, Application/entrainer_forgely.py, Tests/test_video_ui.py.
Interface: VideoPanel(parent, output_root), busy, request_close(callback).
- [ ] Tests rouges : onglets, import, zones relatives sur aperçu, revue/correction et activation des boutons, fermeture pendant analyse.
- [ ] Construire liste MP4, sélection de zones par glisser, curseur d’aperçu, analyse asynchrone, table événements, édition JSON des jets et sélecteurs lisibles pour objet/rune/résultat, rapport et transmission.
- [ ] Préserver le panneau virtuel existant et arrêter proprement le travailleur vidéo à la fermeture.
- [ ] Tests verts et vérification Tk réelle aux tailles usuelles.

### Task 4 — Calibration, rapports et livraison

Files: Application/forgely_labo_live.py, Application/forgely_video_report.py, Tests/test_video_calibration.py, docs/SESSIONS_VIDEO.md.
- [ ] Tests rouges : source vidéo distincte, agrégation par objet/jet/rune/puits, modification/rétraction visible au rafraîchissement, HTML échappé et effectifs/incertitudes.
- [ ] Raccorder la lecture vidéo qualifiée à compute_snapshot et produire rapports HTML/JSON/CSV par session.
- [ ] Vérifier tests ciblés, régressions entraîneur/contexte/lecture puis suite complète appropriée ; compilation et revue indépendante finale.

## Ledger

Ruling: exécution dans la session actuelle sans nouvelle demande d’approbation du plan — l’utilisateur vient d’autoriser explicitement le développement du fonctionnement présenté.

Ruling: le dossier racine n’a pas de .git ; travailler localement avec sauvegarde ciblée des fichiers modifiés, sans publication ni réutilisation de l’ancienne branche publiée.

Ruling: l’utilisateur a ensuite demandé l’intégration des principes de sélection observables du bot installé, sans clics dans le jeu. Ajout d’un module de raisonnement explicable commun et d’un mode de comparaison préparatoire optionnel. La formule compilée complète et le taux de réussite réel ne sont pas connus ; aucun composant externe n’est chargé.

## Résultats d’exécution

- Stockage, lecture MP4, appariement, revue et calibration implémentés avec tests rouges puis verts.
- Revue indépendante : corrections conservées à la reprise et analyses précédentes archivées ; stabilisation post-événement différée ; deux tentatives rapprochées exclues des deux côtés ; rune corrigeable et objet confirmable manuellement.
- Connexions vidéo SQLite explicitement fermées, vérifiées sous Windows.
- Interface vérifiée à 1020×700 et 860×620, y compris bouton de sauvegarde de la revue. Correction par tableau de valeurs, sans saisie JSON.
- Chaîne réelle OpenCV/Tesseract sur MP4 synthétique vérifiée ; aucun transfert de ces données vers la base réelle.
- Lanceur natif reconstruit : utilise les sources actuelles et l’environnement local existant. Exécutable précédent sauvegardé.
- Tests de compatibilité des entraînements classiques et de séparation des politiques expérimentales passés ; benchmark de calcul conservé dans .test-tmp/reasoning-performance.json.
- Vérification complète finale et inventaire détaillés dans le rapport de livraison.
