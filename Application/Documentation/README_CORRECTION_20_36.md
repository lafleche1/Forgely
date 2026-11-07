# Forgely 0.20.36 — En-tête d'objet au-dessus du résultat de rune

Dans l'atelier DOFUS, le bloc de l'objet actif apparaît en tête de la colonne
Historique après la première rune. Les lignes « Échec », « Réussite critique »
ou « Réussite classique » se trouvent sous cet en-tête. Les blocs d'objets
anciens restent visibles plus bas et ne doivent pas être réutilisés.

`forgely_history_identity.py` recoupe le premier en-tête avec les deux lectures
OCR de la zone du nom. Une lecture de secours depuis l'historique n'est acceptée
que si un résultat appartient au même premier bloc. Une contradiction explicite
entre les deux sources invalide la proposition. La création automatique d'une
fiche reste conditionnée à la confirmation répétée du nom et de son icône.

`forgely_detection.py` prend maintenant en charge les résultats insérés sous
un en-tête d'objet qui reste fixe. La détection exige toujours un décalage
stable de lignes déjà vues, sans compter l'historique préexistant au démarrage.
Les libellés « Réussite critique » et « Réussite classique » sont reconnus.

Le diagnostic inclut la ligne `HISTORIQUE OBJET`.
