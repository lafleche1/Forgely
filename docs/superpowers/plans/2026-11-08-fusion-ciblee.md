# Fusion ciblée Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Réunir les modifications PC et GitHub sans perdre les fonctions locales.

**Architecture:** Copie de préparation distincte fondée sur main, fusion à trois
versions lorsque possible, résolution explicite des conflits, tests avant report
local et publication sur une branche dédiée.

**Tech Stack:** Python 3.13, pytest, Git, Windows, Tesseract.

**Spec:** docs/FUSION_CIBLEE_2026-11-08.md

## Global Constraints

- Aucun remplacement par une version ancienne ; sauvegardes et empreintes.
- Aucune publication d'observations personnelles ou de secrets.
- Aucun gain en jeu revendiqué à partir de mesures synthétiques.
- Conserver main et l'archive de distribution actuelle.

## Review Focus

- Invalidation des caches après changements de jet, session et références.
- Séparation des observations réelles et simulations.
- Compatibilité des nouveaux modules distants avec l'apprentissage local.
- Préservation des corrections OCR locales (signes, zéros et lignes partielles).
- Concurrence : changements locaux et distants pendant la fusion.

### Task 1: Inventaire et fusion dans la copie de préparation

**Files:** Application/, Tests/, tests/, docs/, lanceurs et configuration.

**Interfaces:** Consomme les fichiers locaux et les révisions Git distantes ;
produit une branche fusionnée et un inventaire des conflits.

- [x] Vérifier la suite locale : 1543 passed, 25 skipped, 42 subtests passed.
- [ ] Sauvegarder les fichiers et leurs empreintes.
- [ ] Comparer les changements depuis le dernier protocole partagé 1c652809.
- [ ] Fusionner les trois versions en préservant les ajouts des deux côtés.
- [ ] Résoudre chaque conflit à partir de ses tests et des règles actives.

### Task 2: Vérification et corrections de compatibilité

**Files:** Application/tests/, Tests/, tests/ et seuls modules impliqués.

**Interfaces:** Suite pytest et compilation des sources Python.

- [ ] Exécuter la suite réunie avec Tesseract et un dossier temporaire isolé.
- [ ] Pour chaque défaut, reproduire dans un test, corriger puis vérifier.
- [ ] Exécuter la suite complète et compiler tous les modules.
- [ ] Relire indépendamment l'ensemble des différences.

### Task 3: Report local et publication

**Files:** Sources validées, docs/FUSION_CIBLEE_2026-11-08.md.

**Interfaces:** Empreintes locales de départ et commit distant attendu.

- [ ] Vérifier l'absence de modifications concurrentes locales et distantes.
- [ ] Reporter les sources validées localement avec sauvegarde.
- [ ] Publier sur une branche dédiée puis ouvrir une proposition de fusion.
- [ ] Vérifier le commit publié et consigner exactement fichiers, tests et limites.
