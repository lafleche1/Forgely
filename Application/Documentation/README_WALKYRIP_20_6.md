# Walkyrip : première cohorte de sources pour le laboratoire

**État réel : 7 sessions candidates repérées, 0 vidéo analysée, 0 tentative vérifiée, aucune probabilité Walkyrip calculable.**

`walkyrip_sources.csv` recense des dates et titres relevés dans l'historique public de TwitchTracker : https://twitchtracker.com/walkyrip/streams . Le référencement d'une session ne garantit pas que sa VOD soit encore disponible, ni que l'intégralité des tentatives y soit visible.

## Protocole

1. Obtenir auprès du créateur un MP4 ou un accès explicitement autorisé aux VOD. Ne pas contourner les restrictions des plateformes.
2. Vérifier la version du jeu (DOFUS 3 vs Rétro), la date, les coupures et la visibilité de l'historique.
3. Exécuter `py laboratoire_videos.py candidats session.mp4 candidats.csv` et `py laboratoire_videos.py planche session.mp4 planche.jpg`.
4. Examiner chaque séquence, remplir `py laboratoire_videos.py init revue.csv` avec l'état avant/après, la rune, le puits et le résultat, puis faire vérifier.
5. `py laboratoire_videos.py export revue.csv observations_video.csv` n'exporte que les lignes vérifiées.
6. `py laboratoire_walkyrip.py walkyrip_sources.csv --revue revue.csv` audite la collecte.

Les statistiques ne sont pas activées par défaut dans Forgely. Exclure les vidéos montées centrées sur les réussites, les tentatives sans résultat visible et les sessions Rétro de l'entraînement DOFUS 3. Une vidéo longue ne prouve pas que tous les essais ont été observés. Ne jamais inventer des SC/SN/EC.

**Contact du créateur** : passer par les coordonnées publiques de sa chaîne pour demander une autorisation et les fichiers source. Aucun message n'a été envoyé.
