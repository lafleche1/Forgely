# Forgely — fonctionnalités à arbitrer

Ces propositions sont des idées pour la suite, pas des fonctions déjà disponibles.

| Priorité | Fonctionnalité | Utilité | Données/condition requises |
| --- | --- | --- | --- |
| P0 | Calibrage de l'atelier en un clic | OCR fiable selon taille/zoom de la fenêtre | Captures variées, validation en jeu |
| P0 | Lecteur de jet complet (avant/après) | Reconnaître ce qui change réellement après chaque fusion | Détection robuste de toutes les lignes, y compris absentes |
| P0 | Reconnaissance de rune réellement POSÉE | Éviter de confondre rune visible et rune tentée | Capture du clic/fusion via historique visuel, sans automatisation de jeu |
| P0 | Statut « confidence faible » du logo | Aucune recommandation non vérifiée | Score de fiabilité OCR et de correspondance |
| P0 | Profil naturel des équipements par ID | Distinguer FM classique / over / exo | Catalogue de jets min/max fiable, versionné |
| P1 | Prix des runes par serveur | Trouver le chemin le moins cher | Prix fournis ou source autorisée |
| P1 | Coût moyen et risque d'atteinte d'objectif | Arbitrer entre Vi/Pa/Ra et arrêter au bon moment | Probabilités calibrées par état, prix |
| P1 | Sélection de profils d'objectifs (perf, rapide, budget) | Adapter les conseils aux priorités du joueur | Objectifs sauvegardés |
| P1 | Sauvegarde/retour à un jet satisfaisant | Savoir quand conserver un équipement | Historique validé des états |
| P1 | Détection auto de changement d'item | Éviter doublons et mélange des stats | ID image + titre + bonus |
| P1 | Analyse de qualité des observations | Exclure doublons, OCR incertains, biais | Journal complet + filtres |
| P1 | Export CSV/JSON, sauvegarde et restauration | Contrôler, partager et restaurer ses stats | Stockage local |
| P2 | Comparaison de stratégies simulées hors jeu | Tester coûts/risques sans consommer de kamas | Modèle validé, séparé des mesures réelles |
| P2 | Mode communauté avec consentement et anti-fraude | Enrichir des statistiques comparables | Serveur, sécurité, transparence |
| P2 | Replay d'une session (chronologie, puits, runes) | Comprendre les erreurs et progrès | Historique avant/après fiable |
| P2 | Reconnaissance multi-personnages / multi-écrans | Utiliser la bonne fenêtre du jeu | Capture Windows stable |
| P2 | Assistant d'arrêt / gestion du budget | Réduire les pertes excessives | Limites volontaires du joueur |

**Principes** : aucune action automatisée dans le jeu ; pas de taux inventé ; ne jamais injecter des simulations dans les observations réelles ; statistiques communautaires seulement après infrastructure et règles de partage explicites.
