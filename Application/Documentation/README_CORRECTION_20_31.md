# Forgely 0.20.31 — Correction de l'identification de l'objet

## Cause observée

La zone `crop_item_header` était `(0.29, 0.11, 0.56, 0.23)` : elle
contenait l'en-tête du personnage, pas le nom de l'objet. L'équipement
restait donc non confirmé, et le jet/le reliquat étaient exclus de l'état
stabilisé malgré les 33 lectures OCR réussies.

## Correction

- Cadrage du nom de l'objet sur la première ligne du panneau historique.
- Reconnaissance OCR sur deux variantes pour les objets inconnus.
- Confirmation multi-images (3 pour objets connus, 4 pour nouveaux).
- Enregistrement local d'un nouvel objet uniquement après cette confirmation.
- Invalidation immédiate de l'objet précédent en cas de changement détecté.
- Export d'une image `item_...png` et nouvelles lignes de diagnostic.

## Vérification

Testé localement sur la capture DOFUS de l'utilisateur :
`ANNEAU DU CYCLOÏDE` reconnu avec les deux variantes OCR.
Analyse des exemples OCR : `300 Vitalité` et `reliquat : 0` reconnus.
156 tests unitaires passent. Pas de test d'intégration en direct sur Windows.
