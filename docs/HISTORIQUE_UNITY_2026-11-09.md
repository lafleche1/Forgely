# Lecture ciblée de l'historique Unity

La lecture en direct utilise les captures continues existantes et les zones
de l'atelier : historique, colonne du jet actuel, colonne des modifications,
reliquat et logement de l'objet. Les coordonnées sont relatives à la surface
normalisée par `WorkshopLocator`, qui vérifie la structure avant de corriger
les déplacements et changements d'échelle. Les cadres ajoutés aux captures
par l'utilisateur sont des annotations de référence, pas des marqueurs exigés
dans le jeu. Une disposition différente reste à calibrer ; aucune reconnaissance
universelle des interfaces n'est revendiquée.

## Lecture et apprentissage

- L'icône dans la colonne de gauche ouvre une tentative. Les icônes suivantes
  désignent les caractéristiques ; elles ne créent pas de nouvelles tentatives.
- Nombre sans signe : gain. Signe moins : perte. Les mentions de reliquat
  donnent sa direction, jamais une quantité inventée.
- SC : gain vert sans perte ni mouvement du reliquat ; SN : gain et variations
  en texte neutre ; EC : pertes rouges sans gain, ou seulement reliquat consommé.
  Les groupes illisibles, incomplets ou contradictoires restent indéterminés.
- Le gain détermine le type/palier uniquement s'il correspond à une rune unique
  du catalogue. Les icônes d'historique confirmées par l'utilisateur complètent
  cette lecture, notamment pour les échecs PO, Do Pou et Pa Ine. Les nouvelles
  familles ou paliers ambigus ne sont pas devinés.
- La référence initiale ne compte pas les anciennes tentatives. Deux captures
  stables et un recouvrement d'au moins deux groupes sont nécessaires pour
  reconnaître une insertion. Les sauts de plusieurs tentatives ne sont pas
  attribués artificiellement à une seule rune.
- Avant d'apprendre, le circuit existant exige l'objet courant confirmé, un
  profil complet et des états avant/après stables. Pour les événements visuels,
  les variations de caractéristiques et la direction du reliquat doivent aussi
  correspondre exactement au groupe lu. L'audit des poids existant reste actif.
- Les captures statiques et leurs icônes sont des tests/références de vision,
  pas des tentatives réelles à importer dans les fréquences de passage.

Le nom ancien présent dans l'historique n'identifie pas l'objet actuel. Le
lecteur automatique utilise exclusivement l'artwork du logement actuel avec
une comparaison prudente au catalogue ; une ambiguïté impose une sélection
dans le catalogue. La capture 152632 vérifie l'identification de l'Anneau de
Padgref malgré la présence de l'ancien Anneau du Cycloïde dans l'historique.

La colonne des modifications est lue si elle contient du texte et conservée
au diagnostic. Elle ne remplace pas à elle seule les caractéristiques et le
reliquat avant/après pour qualifier un exemple d'apprentissage.

## Latence

L'historique complet n'est plus OCRisé à chaque cycle : en direct, seul le
dernier groupe nouveau est décodé. Des caches bornés réutilisent les pixels
inchangés. La reconnaissance de l'atelier est signalée dès sa vérification
structurelle, avant l'achèvement de l'OCR. Le catalogue des objets est préparé
en arrière-plan au lancement ; ses tableaux numériques peuvent être rechargés
d'un cache local non exécutable, invalidé si les références changent. Un cache
endommagé est ignoré et son remplacement est atomique.

Mesures Windows locales sur la capture 151702, trois lectures froides et
30 réutilisations : historique entier ~797 ms, dernier groupe ~313 ms,
historique inchangé ~0,83 ms avec un seul appel OCR pour 31 lectures. Le
calcul de conseil médian était ~0,41 ms après préparation. Ces mesures sont
hors jeu et ne mesurent pas le délai complet capture/affichage en session.
La capture 152632 a été recadrée automatiquement et ses 13 lignes courantes,
y compris Critique et les malus, ont été lues dans le contrôle manuel local.

## Limites

Les captures fournies sont des références de développement ; leur réussite
ne démontre pas un taux de reconnaissance sur toutes les configurations.
Le défilement, les groupes coupés, les lignes qui changent pendant la lecture,
les icônes inconnues et les OCR contradictoires peuvent suspendre l'attribution
ou l'apprentissage. Les masques et proportions doivent être validés sur de
nouvelles captures indépendantes. Les malus sont lisibles mais les gardes
existantes du moteur de conseil pour les profils signés sont conservées.
Les formules de probabilités n'ont pas été rendues plus exactes par ces
changements de vision. Relancer Forgely charge le code modifié ; aucun
redémarrage automatique de la session utilisateur n'a été effectué.

## Correction du retour terrain 160626

Le petit encadrement blanc de la ligne surjetée faisait disparaître « 11
Dommages Neutre » du bloc OCR, alors que les autres valeurs étaient lues. Le
suivi affichait donc encore l'ancienne mesure de 5, à revérifier, et suspendait
le conseil. La colonne courante détecte maintenant ces bords et relit seulement
leur intérieur sous deux formes (pixels RGB et masque du texte vert). Les deux
lectures doivent être identiques avant de remplacer une valeur.

Un puits partiel stabilisé peut désormais apparaître dans le rapport avec la
mention « provisoire · jet incomplet ». Il ne devient pas pour autant un état
autorisé pour les conseils ou l'apprentissage. L'invalidation des lectures le
remet à inconnu. Tests de référence : 11 Dommages Neutre, 281 Vitalité, 38 Force,
0 % Résistance Eau et puits provisoire 1,3. Le contrôle de disposition de la
fenêtre flottante et les contrôles des lectures périmées restent actifs.
