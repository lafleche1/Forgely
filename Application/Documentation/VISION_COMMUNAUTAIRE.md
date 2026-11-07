# Forgely — Vision communautaire et architecture cible

**Décision produit actée le 6 novembre 2026.** Ce document fait référence pour les futures évolutions de Forgely.

## Positionnement

Forgely est un **assistant communautaire gratuit de forgemagie pour DOFUS 3**. Il n'est **pas destiné à être vendu**. La version de développement actuelle fonctionne localement, mais **l'architecture cible est connectée à un serveur central** : les statistiques issues des tentatives des joueurs doivent être regroupées et bénéficier à toute la communauté.

## Fonctionnement cible

1. Le client observe l'atelier et déduit une tentative (objet, jet avant/après, rune, puits/reliquat, résultat SC/SN/EC, horodatage et contexte utile).
2. Les lectures incertaines sont signalées et corrigées/confirmées avant de devenir des observations fiables.
3. Avec information et accord explicites de l'utilisateur, le client transmet les événements pertinents au serveur par une API sécurisée. Le client garde une file d'attente locale en cas de coupure et évite les doublons lors des renvois.
4. Le serveur valide, déduplique, classe et agrège les tentatives par contexte pertinent, et non seulement par nom de rune.
5. Les clients consultent les statistiques partagées, accompagnées de leur taille d'échantillon, de leur provenance et de leur incertitude.

## Principes non négociables

- **Communautaire et gratuit** : ne pas construire le produit autour d'une vente ou d'un abonnement.
- **Statistiques mutualisées** : aucune estimation communautaire ne doit être présentée comme provenant seulement du joueur courant.
- **Qualité avant quantité** : distinguer événements vérifiés, observations OCR non confirmées, données importées, hypothèses et simulations ; ne pas mélanger ces populations silencieusement.
- **Contexte des tentatives** : conserver les variables utiles à l'analyse pour éviter des probabilités trompeuses.
- **Confidentialité** : minimiser les données transmises ; ne pas envoyer les captures brutes, identifiants de compte ou données personnelles par défaut ; documenter la conservation et la suppression des données.
- **Sécurité et robustesse** : API authentifiée lorsque nécessaire, limitation des abus, contrôles anti-doublons, migrations de schéma et synchronisation résiliente.
- **Transparence** : afficher le nombre d'observations, le niveau de confiance et les limites ; ne jamais annoncer des probabilités exactes non démontrées.
- **Assistance uniquement** : Forgely n'effectue pas d'actions dans le jeu à la place du joueur.

## État actuel vs cible

**Actuellement (v0.20.14)** : application Windows/Tkinter, OCR, diagnostic, recommandations et historique local. **Le serveur communautaire, l'API de synchronisation et les statistiques mutualisées ne sont pas encore déployés.** Les mentions « local » des anciens README décrivent l'état technique historique, pas le positionnement final du produit.

**À construire** : modèle d'événements versionné ; protocole d'envoi avec consentement et reprise hors ligne ; API et base centrale ; validation/anti-doublons ; agrégation et calcul d'intervalles de confiance ; interface de consultation des données communautaires ; politique de confidentialité et contrôles de sécurité.

## Conséquence pour les développements futurs

Toute nouvelle fonctionnalité de statistiques ou de collecte doit prévoir dès la conception la future synchronisation serveur, sans faire dépendre le fonctionnement de base d'une connexion permanente. Préserver la possibilité de supprimer/retirer ses données selon la politique retenue.
