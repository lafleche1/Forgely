# Forgely 0.20.5 — Début de la collecte vidéo assistée

## État réel des données

**0 tentative YouTube vérifiée et importée dans cette livraison.** Aucune vidéo YouTube n'a été téléchargée, analysée image par image ni transcrite en résultats SC/SN/EC. Les URL du catalogue sont des pistes, pas des preuves statistiques.

## Collecte sur un MP4 autorisé

1. Fournir une capture de sa propre session ou un fichier vidéo reçu avec autorisation.
2. Installer les dépendances : `py -m pip install opencv-python Pillow`.
3. Rechercher les moments où l'interface change : `py laboratoire_videos.py candidats session.mp4 candidats.csv --pas 0.5 --seuil 0.14 --ecart 1.0`.
4. Générer une planche : `py laboratoire_videos.py planche session.mp4 planche.jpg --intervalle 5`.
5. Contrôler chaque candidat dans la vidéo. Le détecteur voit des changements d'image (menus, curseur, effets), **pas des runes prouvées**.
6. Créer `py laboratoire_videos.py init revue.csv`, saisir les tentatives complètes, marquer `verifie` uniquement après inspection, puis `py laboratoire_videos.py export revue.csv observations_video.csv`.

Les exports restent indépendants des observations OCR et des simulations. Ils ne sont **pas injectés automatiquement** dans les conseils du joueur. Les taux ne peuvent être calculés qu'après validation et collecte suffisante. Éviter les vidéos montées qui montrent surtout des réussites : fort biais de sélection.
