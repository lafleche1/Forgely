# Lecture du jet : séparation des colonnes

## Observations

La capture initiale montrait un atelier reconnu, mais aucun jet ni puits affiché.
En observation directe, le puits 4,9 et le formulaire de jet souhaité sont apparus.
Le formulaire affichait cependant 7 dommages neutres alors que le jeu en montrait 4.
Cela ne prouve pas à lui seul quelle sortie Tesseract avait produit cette valeur.

Un test a reproduit une cause possible : lorsque la valeur actuelle manque dans
le texte OCR d'une ligne `7 10 Dommages Neutre`, le parseur retient 10, c'est-à-dire
une borne naturelle, comme valeur actuelle.

## Correction

La lecture des valeurs actuelles utilise désormais une zone excluant les colonnes
Min/Max dans la disposition normalisée de l'atelier. Une lecture indépendante du
tableau complet reste conservée pour les bornes d'identification. Ses lignes sont
marquées `[PROFIL]` et exclues du calcul du jet actuel. Une colonne actuelle vide
ne peut plus être remplacée par la lecture du profil complet.

L'activation automatique des prix Tylezia est également retirée du démarrage.
Cet appel hérité déclenchait une écriture de préférences inutile et empêchait
le lancement de diagnostic dans l'environnement restreint. Ce problème de
lancement n'est pas présenté comme la cause de la capture initiale.

## Vérification et limites

22 tests ciblés et 3 sous-tests réussis : séparation des colonnes, conservation
des bornes, non-invention des valeurs, capture de référence Vitalité 342/Tacle 0,
reconnaissance de l'atelier, parallélisme OCR et démarrage sans prix.

L'exécution globale a produit 1765 réussites, 27 tests ignorés et 42 sous-tests
réussis. Ses quatre échecs étaient des tests simulant exactement quatre appels
OCR, ou un ordre fixe d'appels, avant l'ajout de la lecture indépendante. Ces
tests ont été adaptés et repassés dans la validation ciblée ci-dessus.

L'affichage complet après redémarrage n'a pas été confirmé en direct. La capture
native du jeu GPU est indisponible lorsque DOFUS est en arrière-plan dans cet
environnement ; le panneau Python visible n'est pas exposé comme fenêtre ciblable
par l'outil de diagnostic. Aucune rune n'a été passée et aucun objectif utilisateur
n'a été enregistré pendant cette intervention.

Les changements concernent les sources locales ; aucun exécutable n'est reconstruit.
