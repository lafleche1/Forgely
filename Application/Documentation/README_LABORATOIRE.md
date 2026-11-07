# Laboratoire externe Forgely 0.19.7

**Ce dossier n'est pas une fonctionnalité de l'interface de jeu.**

## Audit des observations réelles

1. Dans Forgely, exporter les observations en CSV depuis les outils avancés.
2. Dans ce dossier, lancer :

```bash
python laboratoire_observations.py observations.csv --sortie audit_fm.json --minimum 30
```

Le fichier JSON contient les comptages SC/SN/EC et, pour les groupes d'au moins 30 observations **vérifiées**, les fréquences descriptives et intervalles de Wilson approximatifs à 95 %. Le seuil de 30 ne prouve pas la précision des taux. Les données `ocr_auto` non revues et les simulations sont exclues. L'audit ne modifie pas la base Forgely.

Pour une vidéo publique, seule une transcription **revue manuellement** peut utiliser la source `video_verified`, avec les mêmes colonnes : `date_utc,equipement,rune,resultat,source`. Il n'y a **pas** de téléchargement de VOD, d'OCR vidéo ni d'analyse de streamers automatisée dans cette version.

Attention : ces fréquences ne sont pas des probabilités de succès conditionnelles à un jet/puits. Elles ne doivent pas alimenter automatiquement le conseiller de rune. Les simulations du fichier `laboratoire_fm.py` restent hypothétiques et indépendantes des observations.
