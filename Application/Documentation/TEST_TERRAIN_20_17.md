# Forgely 0.20.17 — Préparation du test terrain

Cette version ajoute un **outil d’audit local en lecture seule**, sans changer les conseils ni la collecte OCR existants.

## Utilisation

Après une session de 100 à 200 tentatives en mode Observation, ouvrir un terminal dans le dossier Forgely et lancer :

```bat
python forgely_audit_terrain.py
```

Deux fichiers seront créés dans `Documents\Forgely-Audit` : `tentatives_a_verifier.csv` et `bilan_collecte.json`. Le CSV contient une ligne par tentative et trois colonnes vides pour vérification humaine, correction et commentaire. Il peut être ouvert dans Excel.

**Important :** les événements `ocr_auto` sont marqués comme **à vérifier**, pas comme validés. Le bilan ne mesure **pas** la précision OCR ni l’efficacité des conseils : cela exige une vérification humaine et des tests comparatifs. Aucune donnée n’est envoyée à un serveur. L’export contient les noms d’objets et les détails des tentatives : ne le partager qu’en connaissance de cause.

## Protocole suggéré

1. Jouer en mode Observation et conserver un relevé manuel de référence des tentatives.
2. Exporter et comparer chaque événement OCR à ce relevé.
3. Mesurer les omissions, doublons, mauvaises runes et erreurs de résultat SC/SN/EC.
4. Corriger les erreurs avant d’utiliser ces données pour entraîner ou évaluer les recommandations.
5. Tester ensuite Copilote et Observation sur des objectifs comparables, sans promettre de gains avant mesure.

L’outil ne modifie pas la base SQLite. Le futur installateur Windows autonome reste à compiler et tester sur Windows.
