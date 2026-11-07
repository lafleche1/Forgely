# Forgely — préparation de mise en ligne

## Ce qui est fourni

- `serveur/` : prototype API JSON, schéma d'événements v1, stockage SQLite pilote, endpoint santé, statistiques agrégées, déduplication UUID, validation stricte, Dockerfile et Compose.
- `serveur/README.md` : démarrage, limites et tests.
- `VISION_COMMUNAUTAIRE.md` : principes produit.
- **Aucun serveur distant n'est activé** ; aucun transfert de données n'a été ajouté à l'application cliente.

## Jalons obligatoires avant lancement public

- [ ] Choisir hébergeur, domaine, budget, pays d'hébergement et responsable de l'exploitation.
- [ ] Écrire les mentions légales et politique de confidentialité (responsable, finalités, données, durée, droits, contact, sous-traitants) ; vérifier RGPD et conditions Ankama.
- [ ] Définir consentement explicite **désactivé par défaut**, retrait, suppression et transparence de l'envoi côté client.
- [ ] Construire la synchronisation locale fiable : file persistante, idempotence UUID, version d'API, retries bornés, arrêt immédiat après retrait du consentement.
- [ ] Sécuriser l'API publique : identité client/joueur pseudonyme, jetons individuels révocables, limitation de débit, anti-spam/anti-fraude, authentification, protection des secrets.
- [ ] Migrer vers PostgreSQL et gérer migrations, sauvegardes chiffrées, restauration testée, rétention et purge.
- [ ] Ajouter validation du contexte FM : valeurs avant/après, poids, puits, cohérence SC/SN/EC, qualité OCR, doublons inter-joueurs, provenance et vérification.
- [ ] Ne pas agréger des contextes incompatibles ; publier n, méthode, biais et intervalles de confiance ; bloquer les groupes trop petits.
- [ ] HTTPS, reverse proxy, pare-feu, supervision, alertes, logs minimisés, tests de charge et plan de reprise.
- [ ] Définir CI, tests d'intégration, pipeline de livraison signée et mise à jour de l'application Windows.
- [ ] Bêta fermée volontaire, puis lancement progressif après audit de sécurité et qualité des données.

## Décisions d'architecture proposées

Client Windows conservant OCR et conseil local pour fonctionner hors-ligne ; API HTTPS dédiée à l'envoi d'événements **consentis** ; serveur de validation ; base PostgreSQL ; agrégats versionnés consultables en lecture. Le prototype `serveur/` sert à valider le contrat, **pas à remplacer** cette architecture de production.
