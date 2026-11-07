# Forgely — serveur communautaire (prototype de préproduction)

Ce dossier est une **base technique non déployée**, pas un service public prêt à ouvrir à tous. Le client Forgely actuel **ne synchronise pas encore** ses observations. Aucun compte, hébergement, nom de domaine ni certificat TLS n'a été créé.

## Démarrage local

```bash
cd serveur
export FORGELY_INGEST_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
export FORGELY_DB=./forgely-dev.sqlite3
python app.py
```

Sous Windows PowerShell, définir les variables avec `$env:FORGELY_INGEST_TOKEN=...` et `$env:FORGELY_DB=...`.

`GET /health` : santé ; `GET /v1/stats?rune=Ra%20Vi` : agrégat brut ; `POST /v1/attempts` : tentative JSON, en-tête `Authorization: Bearer <token>`. Exemple : `example_event.json`. Les UUID identiques sont dédupliqués. Aucune capture d'écran, aucun identifiant joueur n'est accepté dans l'événement. Uniquement les événements `manual` ou `ocr_confirmed` sont acceptés.

## Conteneur

Copier `.env.example` en `.env`, générer une vraie clé secrète puis `docker compose up -d --build`. Port exposé **uniquement sur 127.0.0.1:8080** ; un proxy HTTPS externe est requis pour accès Internet.

## Limites importantes avant exposition publique

- **NE PAS exposer tel quel sur Internet** : jeton partagé de démonstration, pas d'identité par joueur, de quotas, de protection contre le spam ou la fraude, ni de modération.
- SQLite convient au pilote mono-instance seulement ; prévoir PostgreSQL, migrations, sauvegardes et restauration testée pour la production.
- Agrégats bruts, pas de contrôle anti-manipulation, de fiabilité des sources ni d'intervalles de confiance. Une déclaration « manuelle » n'est pas une preuve.
- Pas de retrait sélectif de données par utilisateur (pas de compte) : à concevoir avant collecte publique.
- Pas de télémétrie cachée : **aucun envoi automatique** depuis le client actuel. Consentement explicite et file hors-ligne à construire.
- Prévoir reverse proxy HTTPS, limitation de débit, journalisation sans données personnelles, surveillance, protection contre abus, politique de confidentialité et procédure de signalement.

## Tests

`python -m unittest discover -s serveur/tests -v` depuis la racine du projet.
