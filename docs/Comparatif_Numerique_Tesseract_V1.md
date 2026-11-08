# Tesseract actuel contre V1 numerique calibree

Mesures locales du 7 novembre 2026. Les deux chaines doivent retrouver le jet complet configure et le puits exact. Acquisition ecran exclue.

| Cas | Tesseract mediane | V1 mediane | Relectures exactes Tesseract / V1 |
|---|---:|---:|---|
| gelano | 870.57 ms | 0.278 ms | 8/8 ; 500/500 |
| cycloide | 1028.94 ms | 1.271 ms | 8/8 ; 500/500 |

## Verification supplementaire sur image complete

Sur le Gelano : localisation/suivi + masques + lecture numerique V1, mediane 1.533 ms, p95 2.502 ms ; 100 relectures exactes. Tesseract actuel, mediane 1326.69 ms sur 3 relectures exactes. Cette chaine Tesseract lit aussi les textes des autres zones de l atelier ; la V1 ne reconnait pas encore le texte du journal.

## Ce que ces chiffres prouvent

La V1 lit maintenant les nombres et le puits : sa vitesse ne correspond plus uniquement au masquage. Sur ces profils natifs calibres, elle est beaucoup plus rapide que la chaine Tesseract actuelle. Aucune observation, aucun puits metier, aucun apprentissage ni moteur actif de l application n ont ete modifies par le benchmark.

## Limites essentielles

- Captures CV utilisees pour la calibration : pas de precision independante ni generalisable.
- Repetitions des memes deux images, pas de nouvelles sessions de jeu.
- Tesseract utilise la chaine actuelle de Forgely, pas une optimisation experimentale des seules ROIs numeriques.
- Profils CV partiels et tailles fixes ; resultats inconnus hors calibration.
- Aucune mesure du delai affichage-apparition ni de la capture dans ces chiffres.
- Les repetitions sont des relectures des memes images, pas des centaines de nouveaux jets.
- Les profils CV sont issus de ces images : aucune precision independante en jeu n est demontree.
- La capture MSS et la confirmation temporelle restent a ajouter au delai reel ; le budget total de 5 ms n est pas valide.

Script : Application/benchmark_numeric_ocr.py. Donnees detaillees : docs/comparatif_numerique_tesseract_cv.json.
