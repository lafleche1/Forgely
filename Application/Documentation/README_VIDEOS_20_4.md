# Forgely 0.20.4 — laboratoire vidéo indépendant

Le fichier `videos_sources.csv` répertorie des vidéos publiques **sans prétendre avoir analysé leurs images**. Il contient **zéro tentative extraite**. Les métadonnées proviennent de la recherche publique; une vidéo repérée n’est pas une observation statistique.

## Utilisation avec des enregistrements locaux autorisés

1. Obtenir un enregistrement MP4 auprès de son auteur ou utiliser sa propre capture; respecter les droits et les conditions de la plateforme. Le programme ne télécharge rien depuis YouTube.
2. Installer `opencv-python` et `Pillow` si nécessaire : `py -m pip install opencv-python Pillow`.
3. Générer une planche de repérage : `py laboratoire_videos.py planche session.mp4 planche.jpg --intervalle 15`. Cette planche aide à trouver les séquences intéressantes, **elle ne détecte pas les tentatives**.
4. Créer une feuille : `py laboratoire_videos.py init revue.csv`. Remplir une ligne par tentative, avec identifiant vidéo, temps en secondes, jet avant, puits avant, rune, issue, jet après, et vérificateur. Mettre `statut=verifie` uniquement après contrôle de la vidéo. `date_utc` est l'heure de la tentative si connue, ou une date d'observation explicitement documentée. Ne pas inventer l'heure.
5. Exporter uniquement les lignes validées : `py laboratoire_videos.py export revue.csv observations_video.csv`.
6. Évaluer les fréquences conditionnelles : `py -c "from forgely_probabilites_conditionnelles import audit_conditional; import json; print(json.dumps(audit_conditional('observations_video.csv'),ensure_ascii=False,indent=2))"`.

**Limites :** le statut de vérification est une attestation du réviseur, pas une authentification automatique; l'outil refuse les lignes incomplètes et les doublons de timestamp par vidéo. Les vidéos montées peuvent introduire un biais de sélection. Le laboratoire vidéo est **séparé de l'application Forgely et de sa base OCR locale**; aucune donnée n'est injectée automatiquement dans les recommandations. Il n'existe pas encore de reconnaissance vidéo complète SC/SN/EC image par image.
