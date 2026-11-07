# Forgely 0.19.8 — Reconnaissance d'équipement plus robuste

- Un nom d'équipement déjà enregistré peut être reconnu malgré une légère faute OCR, si une seule correspondance est suffisamment forte.
- Aucune création automatique à partir de texte incertain ; la saisie manuelle reste un recours.
- Les lectures OCR manquantes interrompent la série de confirmations pour empêcher de valider des captures non consécutives.
- La détection d'une icône seule ne permet toujours pas de nommer un équipement inconnu.
- Les modèles de probabilités et l'analyse de VOD ne sont pas implémentés dans cette version.

Tests : `python -m unittest discover -s tests -q`.
