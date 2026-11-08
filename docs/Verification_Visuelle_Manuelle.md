# Lecture et calibration automatiques

La version 22.13 configure le profil explicitement sélectionné avant d’accumuler
les lectures. La confirmation de l’icône ne remet ainsi plus à zéro le jet déjà
stabilisé : le parcours manuel peut publier les valeurs et un conseil sur la
troisième lecture cohérente. Les contrôles d’icône et de bornes incompatibles
restent actifs. Le démarrage flottant rend également le focus à DOFUS pour que
la capture GPU puisse reprendre après la sélection.

Le diagnostic sur la capture native actuelle retrouve les 11 caractéristiques
du Cycloïde et son puits de 0,9. Le test du consommateur réel des messages, avec
la sélection manuelle, le jet souhaité et les stabilisateurs réels, vérifie le
passage à une proposition de rune en trois lectures, sans identification OCR du nom.

Depuis la version 22.12, une rune invalide les valeurs utilisables pour les
conseils, sans relancer la demande du nom ni du jet souhaité. La carte de l’objet
et les cibles sont conservées. Les dernières valeurs restent affichées comme
périmées pendant **Actualisation du jet**, puis sont remplacées par les nouvelles
lectures stabilisées. Aucune ancienne valeur n’est utilisée pour conseiller.
De nouvelles captures sont demandées pendant la stabilisation afin de ne pas
attendre le délai d’inactivité entre deux lectures. Une page partielle déjà
stable n’entraîne pas de demandes en boucle pour des lignes hors écran.

La version 22.11 réserve une ligne fixe au bouton **Enregistrer et conseiller** :
seules les caractéristiques défilent. La case **Jet parfait** remplit les champs
sans fermer l’éditeur ; les valeurs sont appliquées à la validation. Le panneau
s’ouvre à droite et reprend sa largeur compacte après l’édition. L’application
rend alors le focus au compte DOFUS capturé, si l’utilisateur n’a pas entre-temps
activé une autre application. La capture ne doit pas lire l’image du copilote.

Pour ce préréglage, une correspondance unique de plusieurs bornes Min/Max
naturelles peut fournir la fiche théorique. Les valeurs actuelles et les noms
de l’historique ne participent pas à cette recherche. Cette correspondance ne
certifie pas l’identité officielle de l’objet et ne crée pas d’observation FM.

Depuis la version 22.10, le copilote propose une case à cocher **Jet parfait**.
La cocher remplace le jet souhaité par tous les maximums théoriques de
l’objet identifié ou choisi explicitement. Le menu flottant et l’éditeur des
cibles offrent également ce raccourci. Une ligne non encore lue peut recevoir
une cible théorique, sans recevoir une fausse valeur actuelle. En l’absence
d’identité ou de fiche théorique, aucune valeur maximale n’est inventée.
La décocher conserve les valeurs et permet de les ajuster librement. Le contrôle
est aussi une case dans les éditeurs. Il se réinitialise au changement d’objet.
L’ancien choix « Jet propre » n’est plus présenté. Les cibles personnalisées
restent modifiables dans l’éditeur du jet souhaité.

La version 22.09 corrige l’arrêt du calcul après l’enregistrement des cibles :
le mode d’interface « Jet propre » n’était pas reconnu par le moteur, provoquant
une exception avant la mise à jour du conseil. Tous les modes de l’interface
sont désormais traduits vers le mode de classement du moteur. Les tests couvrent
le jet complet de la capture, la cible de 350 Vitalité, le puits de 0,9 et le
rafraîchissement effectif du texte du copilote.

Depuis la version 22.08, un jet et un puits stabilisés déclenchent la demande
du jet souhaité dans le panneau flottant. L’utilisateur règle les valeurs puis
enregistre pour activer les conseils, sans sélectionner le nom de l’objet.
Les objectifs de ce mode restent liés à l’icône et au compte de cette session,
et sont effacés lors d’un changement d’objet. Une pause de capture conserve les
objectifs mais suspend les conseils jusqu’à une nouvelle lecture stable.
Le bouton Jet souhaité permet de rouvrir cet éditeur.

Sans nom confirmé, le moteur conseille sur les lignes effectivement lues et
ne prétend pas avoir vérifié le profil naturel complet. Les objectifs sont
des minima : seule la plus petite rune peut finir légèrement au-dessus de la
cible lorsque les bornes naturelles sont inconnues. Les anciennes politiques
de conseil conservent leur comportement par défaut.

Validation de la version 22.08 : 1 428 tests réussis, 24 ignorés et 42 sous-tests
réussis. Le parcours anonyme et l’éditeur intégré sont couverts par les tests ;
le processus actuellement ouvert doit être redémarré pour charger ces sources.

Redémarrer Forgely avec `OUVRIR FORGELY.bat` pour charger la version 22.08.
Les demandes de vérification manuelle sont retirées du copilote, de la barre
latérale et des menus. Les anciennes images restent des archives de calibration
et ne remplacent jamais le jet vivant. Les lectures stables sont utilisées
automatiquement ; aucune annotation humaine n’est nécessaire pour les débloquer.
Les inconnues et contradictions sont relues automatiquement. Elles ne deviennent
pas des mesures fiables simplement parce que les demandes ont été masquées.

L’association bénéficie désormais de la stabilité de l’icône observée par le
fil de capture, indépendamment de l’OCR. Trois captures cohérentes peuvent
remplacer trois analyses OCR pour un objet choisi ou une icône déjà connue.
Le contrôle des bornes naturelles reste actif. Une nouvelle identité issue
uniquement du texte conserve sa confirmation sur plusieurs analyses.
Le cache rapide est lié au compte, à la génération de capture et à une icône
actuelle concordante, avec une validité maximale de deux secondes.

Les références inconnues continuent leur tentative de calibration automatique,
avec accord numérique et OCR, sans panneau de saisie utilisateur.

Validation de la version 22.07 : 1 423 tests réussis, 25 ignorés et 42 sous-tests
réussis. Le démarrage réel et le copilote sans panneau manuel ont été contrôlés.
Le gain de délai d’association en jeu n’a pas encore été chronométré.

## Ce qui est appris

Les formes des chiffres, signes et séparateurs sont partagées entre objets d'une
même configuration de lecture. Une forme nécessite deux exemples confirmés de
pixels différents et concordants. Les libellés sont associés à la caractéristique
choisie. Des étiquettes contradictoires mettent les formes concernées à l'écart.
Une relecture de l'image complète vérifie aussi qu'un nombre n'a pas été tronqué.

La file contient au plus 100 demandes en attente et le catalogue au plus 5 000
exemples. Seules les petites zones des caractéristiques et du reliquat sont
enregistrées ; aucune capture du bureau n'est ajoutée à ce catalogue.

Le catalogue est enregistré dans `%LOCALAPPDATA%\Forgely\vision_v1\reviews.sqlite3`.
Il survit aux redémarrages. La V1 consulte les références activées pendant
l'observation et expose ses lectures dans **Diagnostic OCR**, rubrique
**V1 / vérifications manuelles**. La lecture active est hybride : les champs
visuels peuvent compléter un champ manquant de l'OCR, mais une contradiction
sur le jet ou le puits invalide la lecture de l'image. L'identité confirmée,
la complétude et la stabilisation restent nécessaires avant les conseils.
Tesseract reste actif pour l'historique et le secours.

## Lignes génériques et référentiel théorique

Le lecteur des lignes n'utilise ni nom d'objet ni valeur attendue. Il reconnaît
le nombre à partir du catalogue de glyphes et le libellé complet. Le regroupement
du texte exclut Min/Max sans pourcentage horizontal fixe et conserve les signes
négatifs. Les cas non résolus ne peuvent plus bloquer toute la file automatique.

Trois exports complets ont servi à la calibration initiale (Gélano avant rune,
Cycloïde avant/après), plus deux lignes négatives du Padgref. Deux autres exports
sont réservés au contrôle : Gélano après rune et Cycloïde précédent. Les jets et
reliquats sont reconnus sur ces images ; cela ne valide pas toutes les tailles
d'interface ni tous les objets. Les mesures sans capture figurent dans
`calibration_autonome_exports.json`.

Les bornes de l'éditeur de jet souhaité servent également à signaler les lignes
manquantes et prioriser les lectures. Elles ne donnent aucune valeur actuelle
et ne suppriment ni zéro, ni perte, ni over/exo observé. Le catalogue local
contient 2 861 équipements, dont 2 725 avec des bornes ; cela ne prouve pas la
complétude de chaque fiche.

## Équipement détecté automatiquement

La carte Équipement actuel suit l'identité confirmée dans l'atelier, avec son
nom du catalogue et son icône. Le bouton **Modifier le jet souhaité** ouvre les
objectifs de cet équipement sans quitter le mode automatique. L'ancien objectif
n'est pas affiché comme celui d'un autre objet. Une identité encore incertaine
affiche **Identification en cours**. Si un éditeur resté ouvert concerne l'objet
précédent, la prochaine ouverture le remplace par celui de l'objet actuel.

## Correction du refus de « 40 Intelligence »

Le refus était causé par l'arrondi flottant de la recherche OpenCV : une
correspondance identique pouvait avoir une distance de l'ordre de 2e-17 au lieu
de zéro. La recherche admet désormais cette erreur d'arrondi, puis vérifie
toujours les pixels du libellé par XOR exact. Le test de régression utilise
la ligne réelle fournie et vérifie qu'elle peut être confirmée.

## Validation native du Padgref et états de lecture

Deux captures natives de l’atelier 1 902 × 1 033 ont ajouté les variantes de
texte du Padgref. Le test réunit 16 caractéristiques sur deux pages, dont le
PM supplémentaire, Tacle −4 et Esquive PM −3. Ces images servent à la
calibration : leur relecture ne constitue pas une validation indépendante.
La zone de collecte descend désormais jusqu’au bas du tableau ; la dernière
ligne était auparavant coupée.

Les valeurs stabilisées avant l’identification du nom sont affichées comme
lues. La confirmation de l’identité reste distincte et nécessaire aux conseils.
Le logo flottant utilise la même identité qualifiée que la carte principale,
au lieu de reprendre un ancien nom. Les demandes de vérification devenues
lisibles avec des références fiables sont retirées pendant l’observation.

Validation du 8 novembre : 1 418 tests réussis, 24 ignorés, 42 sous-tests
réussis. Les derniers ajustements d’invalidation du cache ont aussi été
revérifiés par 21 tests ciblés et une relecture du code. Ce résultat ne
constitue pas une garantie de reconnaissance de tous les objets et affichages.
