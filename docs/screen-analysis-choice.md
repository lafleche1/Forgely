# Choix de lecture d'écran pour Forgely

Conserver une architecture hybride : capture de la dernière image, repérage de
l'atelier, comparaison des zones, reconnaissance d'icônes, lecture ciblée des
valeurs, puis OCR textuel pour les libellés et l'historique.

Mesure sur la capture fournie `effects_vitalite_342.png`, 442 × 680, Tesseract avec
un thread OpenMP :

| Lecture | Durée | Constat sur cette capture |
|---|---:|---|
| OCR général sans cache | 553–586 ms | Vitalité manquée |
| Première ligne ciblée | 132–159 ms | 342 Vitalité lue |
| Lecteur complet d'effets | 738–860 ms | Vitalité et dix autres statistiques récupérées |
| Cache exact | 2,1 ms médiane | Réutilisation, pas nouvelle reconnaissance |
| Icônes de runes, 105 références | 75–77 ms | Benchmark de comparaison uniquement |

Priorité suivante : segmenter les lignes une fois par disposition confirmée,
garder leurs libellés et relire seulement les nombres modifiés, avec retour à
la ligne complète si le signe ou la décimale est ambigu. Calculer une fois les
caractéristiques de l'icône courante et mettre celles des références en cache.

La capture récente, le filtrage des changements, les zones parallèles et les
caches existent déjà. Cette mesure sur une seule image n'établit pas un taux
de fiabilité en jeu. L'accès aux caractéristiques via l'accessibilité Windows
n'a pas pu être validé : DOFUS n'était pas ouvert lors de la vérification.

Le simulateur contrôle la cohérence et conseille ; ses prédictions ne remplacent
jamais une lecture manquante par une valeur supposée réelle.
