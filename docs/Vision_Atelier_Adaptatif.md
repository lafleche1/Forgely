# Atelier adaptatif et jet paginé

Mise à jour 22.06 : le fonctionnement actuel de la calibration automatique et
de la lecture hybride est décrit dans `Verification_Visuelle_Manuelle.md`.
Les notes ci-dessous décrivent la première intégration du lecteur paginé.

Les sources de l'application conservent maintenant les lignes confirmées d'un
même objet au fil du défilement. Chaque page doit être lue trois fois ; relire
le même identifiant de capture ne compte pas comme trois observations.

Le tableau distingue les lignes lues, hors écran, à lire et à revérifier. Un
zéro est une valeur lue, jamais une valeur par défaut. Une variation de jet ou
de reliquat, ou un résultat de rune, invalide la fraîcheur des lignes conservées.
Un changement d'objet, de contexte ou une absence confirmée du logement réinitialise
la mémoire. De nouvelles caractéristiques visibles ne prouvent plus un changement
d'objet : le contrôle compare les bornes contradictoires et l'icône.

Un profil de référence est nécessaire pour autoriser un jet assemblé à alimenter
les conseils. Sans profil, la lecture reste partielle. La présence de toutes les
lignes du profil ne permet pas de deviner un exo encore jamais affiché : il faut
parcourir tout le jet lors de l'installation de l'objet. Après une rune, les
anciennes valeurs hors écran doivent être relues. Une lecture assemblée sur plusieurs
pages n'autorise pas l'enregistrement d'une transition atomique avant/après.

Le repérage existant de l'atelier a été corrigé sur une capture réelle où le
panneau des quêtes était contigu : sa couleur pouvait étendre faussement l'en-tête.
Il reste fondé sur la structure DOFUS prise en charge ; une interface ambiguë ou
une autre structure nécessite une nouvelle calibration.

## V1 OpenCV

`NumericReader.read_visible(image)` retrouve les gardes des libellés dans la zone
des caractéristiques et déplace leurs zones numériques en conséquence. Un libellé
absent, tronqué ou présent deux fois est refusé. Les nombres de longueur variable
sont lus en entier, sans réutiliser la largeur du nombre de calibration.

La commande `python -m forgely_cv run` accepte plusieurs `--profile` et un
`--numbers` correspondant à chacun, dans le même ordre. Ajouter `--adaptive-rows`
pour suivre les libellés après défilement. Pour un atelier déplaçable indépendamment
de l'inventaire, calibrer le rectangle `--game` sur le panneau de l'atelier et ses
sous-zones sur ce panneau. Chaque taille native de police requiert ses références ;
aucun redimensionnement ne fabrique de nouveaux glyphes.

Ces références ne couvrent pas encore toutes les interfaces. Les tests de
translation/défilement sur l'image de calibration sont des tests de géométrie,
pas une mesure indépendante de reconnaissance.

## Historique et moteur actif

La V1 masque les couleurs du journal mais ne dispose pas encore du dictionnaire
complet ni de l'interprétation des tentatives SC/SN/EC. Elle ne remplace donc pas
encore le moteur de lecture de l'application. L'application utilise toujours son
OCR existant ; les améliorations de mémoire et de tableau sont intégrées à celui-ci.

La prochaine étape utile est un moteur hybride : OpenCV pour jet/reliquat,
Tesseract pour le seul historique modifié. Le basculement doit attendre une
validation des glyphes et libellés aux tailles réelles de l'interface.

Pour cette validation, enregistrer des PNG natifs avant et après quelques runes,
avec l'historique visible, puis le haut et le bas du même objet. Noter la rune
posée et son résultat constaté. Ces données permettront de mesurer séparément
la latence et les erreurs des deux lecteurs.
