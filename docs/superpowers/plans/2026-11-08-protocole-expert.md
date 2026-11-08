# Protocole expert Implementation Plan

**Goal:** intégrer le protocole corrigé et rendre les règles actives auditables.
**Architecture:** moteur existant conservé ; filtre de priorité naturelle ; module
pur de présentation/scénarios ; diagnostic avant/après connecté aux lectures.
**Tech Stack:** Python, Tkinter, pytest, JSON.
**Spec:** docs/superpowers/specs/2026-11-08-protocole-expert-design.md

1. Tests RED : priorité des remontées avant finitions dans les deux modes,
   maintien des exos possibles sans puits et puits supérieur à 101.
2. Tests RED puis implémentation : tableau SC sans consommation du puits,
   budget débité une seule fois, SN/EC sans perte inventée, données invalides ou
   provisoires bloquées, arrêt à l'objectif, absence de confiance numérique.
3. Diagnostic des transitions : arithmétique sur données complètes uniquement,
   valeurs OCR partielles décrites sans preuve fictive ; liaison au bon objet.
4. Intégrer le détail au conseil de l'app ; mode observation respecté.
5. Inventorier les règles en vigueur et leurs conflits ; table runtime des poids
   et couverture des 105 prix ; aucun changement de pondération d'apprentissage.
6. Suite complète, compilation, revue indépendante, commit GitHub atomique,
   paquet Windows testé avec sauvegarde et validation des versions locales.

Review focus : pas de récursion du calcul de scénarios, pas de coût négatif,
pas de statistiques synthétiques en base, pas d'écrasement du reliquat OCR,
pas de scénario ancien après changement d'objet.
