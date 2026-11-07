# Forgely 0.20.16 — Mode Observation passive

Bouton **Mode : Copilote / Mode : Observation** dans l'en-tête. Le choix est sauvegardé dans `LOCALAPPDATA/Forgely/mode_observation.json` et restauré au démarrage.

En mode Observation, aucune recommandation de rune n'est calculée ou affichée dans l'accueil, le détail ou le mini-overlay. La lecture OCR, la collecte de tentatives, le diagnostic et les statistiques locales continuent normalement. Le mode Copilote restaure les conseils.

**Important :** aucune synchronisation avec le serveur communautaire n'est encore active. Les données restent locales. Une lecture OCR erronée peut toujours entraîner un enregistrement erroné : utiliser le diagnostic OCR.
