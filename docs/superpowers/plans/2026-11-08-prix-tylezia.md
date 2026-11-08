# Prix Tylezia Implementation Plan

**Goal:** utiliser les 105 prix de référence dans le copilote existant.
**Architecture:** JSON de référence, migration idempotente des préférences,
mode Budget optimisé existant, métadonnées conservées dans les deux écrans.
**Tech Stack:** Python, Tkinter, JSON, pytest.
**Spec:** docs/superpowers/specs/2026-11-08-prix-tylezia-design.md

- [ ] Tester avant implémentation : catalogue complet et montants, migration
  d'un profil neuf et existant, sauvegarde, conservation des modifications,
  persistance des métadonnées et conseil réel affecté par un changement de prix.
- [ ] Ajouter les prix et leur chargement validé ; activer au démarrage, conserver
  les métadonnées à l'enregistrement et montrer leur origine dans l'interface.
- [ ] Exécuter les tests de régression et la suite disponible ; distinguer les
  ressources manquantes de la récupération partielle du dépôt.
- [ ] Publier les fichiers dans un commit atomique après contrôle de la branche.
- [ ] Préparer une mise à jour Windows avec sauvegarde des fichiers remplacés.

Review focus : aucune donnée économique dans les stats d'apprentissage,
aucune modification ultérieure des prix écrasée, aucune confusion de serveur,
aucun prix moyen présenté comme offre d'achat garantie.
