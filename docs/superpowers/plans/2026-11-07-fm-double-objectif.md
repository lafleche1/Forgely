# Double objectif FM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** proposer deux classements de runes utilisables dans Forgely.
**Architecture:** règles partagées, classement explicable, budget de session et intégration Tk existante.
**Tech Stack:** Python, Tkinter, SQLite, pytest ; aucune dépendance de production ajoutée.
**Spec:** docs/superpowers/specs/2026-11-07-fm-double-objectif-design.md

## Global Constraints
- Conserver les lectures confirmées et la séparation observations/simulations.
- Ne jamais inventer de probabilités ni affirmer un gain terrain non mesuré.
- Profil partiel : ne pas inférer une absence naturelle.
- Aucun changement de l'OCR ni action automatique dans DOFUS.

## Review Focus
- NaN, infinis et booléens : refuser les nombres invalides.
- Prix absent et budget épuisé : suspendre les conseils concernés.
- Petit écart inférieur à la plus petite rune : autoriser un dépassement uniquement si les bornes naturelles connues le permettent.
- Historique ancien : ne pas imputer son coût à la session actuelle.
- Valeurs de jet différentes : ne pas mélanger leurs fréquences.

### Task 1: Contraintes partagées
Files: Application/forgely_rules.py, forgely_decision.py, forgely_fm_model.py; tests/test_fm_objectives.py.
- [x] Écrire et exécuter les tests : Force 101→102 refusé même si over faible ; naturel 120 autorisé ; exos cumulés >101 refusés ; profil partiel sans fausse classification.
- [x] Implémenter validation et poids partagés ; conserver les interfaces existantes.
- [x] Exécuter les tests des règles et moteurs existants.

### Task 2: Classements et budget
Files: Application/forgely_decision.py, forgely_tools.py; tests/test_fm_objectives.py.
- [x] Tester que des prix différents changent le classement économique ; prix absents restent inconnus ; limite restante respectée ; objectif atteint arrête.
- [x] Ajouter mode/prices/remaining_budget en arguments optionnels de advise et candidates ; exposer l'explication et les alternatives.
- [x] Ajouter observation_cursor et cost_since, sans imputer les observations antérieures.
- [x] Vérifier les tests et préserver les anciens réglages.

### Task 3: Intégration et contexte
Files: Application/forgely.py, forgely_labo_live.py, forgely_connaissances.py; tests dédiés.
- [x] Tester l'intégration du mode, des prix, du budget et du profil partiel ; tester la séparation des valeurs de jet.
- [x] Brancher les préférences et le budget de session dans strategy_current, unifier la saisie des prix, ajouter le choix du mode dans le conseil.
- [x] Versionner et enrichir les faits sourcés sans taux arbitraires.
- [x] Exécuter toute la suite et la compilation ; revue finale puis branche et PR de proposition.

## Validation finale

- Suite complète : 339 tests réussis, 14 ignorés (affichage graphique/captures privées), 19 sous-tests réussis.
- Compilation Python et `git diff --check` réussis.
- Revue indépendante : aucun défaut critique ; tentative non attribuée oubliée dans le coût de session corrigée et testée RED→GREEN.
- Robustesse des prix invalides et du reliquat historique booléen également testée RED→GREEN et corrigée.
- Règle retenue : le budget couvre les tentatives enregistrées depuis le lancement, tous objets confondus ; il ne garantit pas la couverture des tentatives manquées.
- Limites : aucun test interactif Windows/DOFUS sur cet hôte ; aucune hausse de réussite terrain revendiquée.
