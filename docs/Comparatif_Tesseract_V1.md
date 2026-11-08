# Comparatif local : Tesseract et V1 OpenCV

Mesure du 7 novembre 2026 sur les fichiers de capture disponibles dans le projet.

**Conclusion : Tesseract reste le seul des deux pipelines actuellement capable
de produire un jet et un puits. La V1 est plus rapide pour localiser et masquer
l'interface, mais n'a pas encore de lecteur numérique intégré. Les deux temps
ne correspondent donc pas au même travail.**

| Chaîne et mode | Répétitions | Médiane | p95 | Résultat fonctionnel |
|---|---:|---:|---:|---|
| Tesseract, nouvelle analyse sans cache | 8 | 1 186,71 ms | 1 291,66 ms | Jet et puits exacts sur les 8 relectures |
| Tesseract, pixels identiques et caches actifs | 50 | 11,85 ms | 425,79 ms | Jet et puits exacts sur les 50 relectures |
| V1, localisation globale à chaque analyse | 30 | 39,75 ms | 42,80 ms | Ancre détectée ; jet et puits non disponibles |
| V1, suivi local après localisation | 100 | 4,07 ms | 4,98 ms | Ancre détectée ; jet et puits non disponibles |

## Ce qui a été vérifié

- Capture complète du Gélano, 1 902 × 1 033 pixels. Référence connue : 10 Vitalité,
  0 PA, puits 0. La chaîne Tesseract comprend les lectures des zones et leur
  parsing, avec la récupération de lignes de Forgely.
- Les huit essais sans cache sont **huit relectures d'une même image**, pas huit
  situations différentes. Ils n'établissent pas une précision de 100 % en jeu.
- Une seconde capture, limitée au tableau des effets, vérifie les valeurs
  attendues Vitalité 342 et Tacle 0. Tesseract retrouve les deux, en 760,99 ms.
  Les autres caractéristiques de cette image ne disposent pas ici d'une
  annotation complète indépendante.
- Pour la V1, l'ancre est découpée dans la même capture que celle du test : cela
  mesure le coût d'un repérage calibré, pas sa robustesse sur d'autres images.
- Le lecteur de glyphes est exécuté avec un dictionnaire vide : il conserve les
  inconnus et n'accepte aucun texte. Le pipeline V1 n'intègre pas encore la
  conversion des caractéristiques et du reliquat en valeurs numériques.

## Limites de la comparaison

La capture écran, l'attente d'un nouveau frame, la stabilisation sur plusieurs
images et l'affichage dans l'application sont exclus des deux chronométrages.
Les répétitions chaudes sur pixels identiques n'équivalent pas à des poses de
runes successives. Le coût supplémentaire de la capture MSS déjà mesuré
séparément empêche de conclure à une latence totale inférieure à 5 ms.

Ni le taux d'erreurs sur de nouveaux objets, ni l'effet sur les FPS de DOFUS
n'ont été mesurés. Aucun puits, aucune observation et aucun entraînement de
l'application n'ont été modifiés par ce comparatif.

## Décision proposée

Conserver Tesseract pour les valeurs actuellement nécessaires. Poursuivre la
V1 comme couche de localisation/masquage ; calibrer ensuite les chiffres,
signes et séparateurs sur des exemples réels. Comparer les jets complets sur
des captures différentes de celles utilisées pour constituer le dictionnaire
avant de remplacer le lecteur de production.

Résultats détaillés : `comparatif_tesseract_cv_v1.json`.
Script reproductible : `Application/benchmark_ocr_vs_cv.py`.
