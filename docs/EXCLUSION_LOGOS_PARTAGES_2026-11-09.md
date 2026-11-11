# Logos partagés et identification automatique

Les références dont les pixels du logo normalisé sont identiques mais dont
les noms diffèrent sont exclues de l'identification automatique. Cette règle
est calculée sur le catalogue entier avant tout filtre de catégorie ou de
bornes naturelles. Les fichiers portant des identifiants de logo différents
mais contenant la même image sont également concernés.

Les références exclues restent des contre-exemples visuels afin qu'une image
ambiguë ne favorise pas artificiellement un autre objet ressemblant. Elles
ne peuvent pas être choisies par un départage OCR. Le catalogue de sélection
manuelle reste intact. Le cache préparé applique la même règle au chargement.

Le catalogue présent contient 262 références exclues et 2 592 références
non exclues par cette règle. Les autres contrôles de fiabilité restent actifs.
Cela supprime cette ambiguïté connue du catalogue sans garantir l'absence de
toute erreur de reconnaissance visuelle.

