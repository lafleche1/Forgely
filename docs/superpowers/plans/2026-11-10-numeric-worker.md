# Lecture numérique séparée — demande utilisateur après test A/B

Intégrer un lecteur jet/puits indépendant de l'observateur historique.
Un seul lecteur publie les mesures numériques ; l'historique garde ses propres
captures et ne peut ajouter des confirmations numériques retardées.
Partager le backend OCR qui fusionne les travaux aux pixels identiques,
conserver les caches locaux et la dernière capture disponible (sans file de
captures en attente), vérifier identité/contexte/génération/provenance à la
publication et lors de l'affichage. Aucun seuil de confirmation abaissé.

1. Reproduire la nouvelle capture et le PA0 avec normalisation réelle.
2. Ajouter un mode lecture numérique seule, puis un worker consommant la boîte
   de dernière image existante ; conserver les lectures complètes pour diagnostic.
3. Supprimer la publication numérique par l'observateur quand ce worker est actif.
4. Vérifier l'avancement malgré historique bloqué, l'arrêt, le changement de
   compte, les valeurs périmées, et la lecture PA0/puits88 de la nouvelle capture.
5. Mesurer avec historique concomitant ; rapporter la portée réelle du test.
