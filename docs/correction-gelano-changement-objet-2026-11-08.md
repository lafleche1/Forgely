# Gelano et changement d'équipement — 8 novembre 2026

La capture de 21 h 19 montre un Gelano avec 15 Vitalité ajoutée, 0 PA et un
reliquat de 0, tandis que le panneau affiche Lavanneau et des lignes absentes
de l'objet visible. Une sélection manuelle peut aussi afficher son propre nom :
la capture seule ne prouve pas quel mode était actif. Le lancement démarre
désormais en détection automatique, conformément au mode demandé.

## Causes reproduites

1. L'identification exigeait trois bornes naturelles. Le Gelano n'a qu'une
   caractéristique naturelle ; l'OCR fusionnait même le zéro et PA en « OPA ».
2. La garde géométrique d'atelier supposait plusieurs lignes et des valeurs
   vertes. La table courte, bleue/blanche, était rejetée par le lecteur rapide.
3. Une optimisation conservait l'identité lorsque la petite ancienne découpe
   d'icône semblait inchangée, avant même de considérer le nouveau résultat
   du comparateur de logo complet. Les valeurs et objectifs précédents pouvaient
   donc rester liés au nouvel objet.
4. Le lecteur rapide pouvait lui-même ne pas relancer l'identification si la
   petite ancienne découpe restait proche.

## Modifications

- Pour peu de bornes lisibles : segmentation du premier plan du logo, plusieurs
  cadrages de pHash et présélection avec conservation des égalités. Validation
  par comparaison RGB masquée, erreur ≤ 20 et marge ≥ 10. Les emplacements et
  dimensions doivent correspondre à un véritable composant du logo, pour
  éviter qu'un sprite sombre corresponde simplement au fond du panneau.
- Une borne naturelle effectivement lue reste un veto si elle contredit le
  candidat. Aucun nom n'est tiré de l'OCR du nom de l'objet.
- Le cas avec trois bornes ou plus conserve ses seuils antérieurs. Une
  ambiguïté entre sprites identiques reste une abstention.
- Une preuve explicite d'identification du catalogue accompagne les messages
  d'identité. Elle autorise la remise en question de l'ancien nom même si la
  petite découpe semble similaire. Du texte sans cette preuve ne bénéficie pas
  de cette priorité, notamment lors d'un masquage ou d'une infobulle.
- Le changement confirmé de nom vide l'ancien jet, les bornes attendues,
  les contextes de capture, les objectifs et les choix de jet parfait.
- Le mode automatique ne récupère plus un nom depuis une ancienne association
  locale lorsque le catalogue ne reconnaît pas le logo actuel.
- L'optimisation du lecteur rapide compare désormais le logo complet et les
  pixels des colonnes Min/Max, avec le contexte de capture.
- Si les gardes géométriques échouent sur la petite table, le titre de
  profession est vérifié indépendamment. Une zone dédiée conserve ce titre
  complet lors du recadrage. La capture rapide ne réutilise cette preuve que
  pour les mêmes pixels et le même contexte (boîte, génération, fenêtre).

## Calibration du chiffre zéro

Le profil `white_zero_pa_9x11_v1` est une calibration manuelle de la forme du
chiffre 0 et du libellé complet PA, issus des pixels de la capture fournie.
Il ne contient aucune règle « Gelano = 0 PA » ni valeur déduite des bornes.
Le lecteur de lignes exige des masques exactement identiques. Un chiffre ou
un libellé modifié est refusé. La provenance et l'empreinte de la capture sont
dans `provenance.json` du profil.

Il ne s'agit pas d'un entraînement automatique d'un modèle général. Relire
l'image ayant servi à la calibration ne démontre pas une précision indépendante.
Cette limite est explicitement conservée dans le résultat de validation.

## Validation et limites

`docs/gelano-validation-2026-11-08.json` conserve le passage de la capture
complète dans le lecteur réel : nom Gelano, preuve catalogue vraie, jet
`{"Vitalité": 15, "PA": 0}`, reliquat 0.0 et lecture stable après trois
observations. Le chemin OCR du nom est remplacé par une erreur pendant cette
vérification : aucun appel n'a eu lieu.

`Tests/test_sparse_slot_change.py` couvre la capture courte, le titre de
profession et ses preuves limitées au contexte, les valeurs, le rejet des
glyphes/libellés altérés, la remise à zéro du jet et des objectifs, le rejet
des anciens noms locaux en automatique et la revalidation du logo complet
par le lecteur rapide. Chaque défaut principal a été reproduit avant correction.

La revue n'a pas identifié d'autre défaut concret dans le comparateur sparse,
le signal de provenance et la calibration. Une incertitude reste : sa marge RGB
est évaluée parmi les candidats de la présélection pHash. Une image visuellement
proche hors présélection n'a pas été exclue par une validation exhaustive en jeu.
Les égalités, dont les sprites identiques connus, sont conservées. Les résultats
ne garantissent pas la détection de tous les équipements et de toutes les échelles.

Journal final : `.test-tmp/sparse-slot-final-validation.log`.

Dernier passage complet sur les sources finales : **1 793 tests réussis,
25 ignorés, 42 sous-tests réussis**, sans échec, en 124,51 s. Le groupe ciblé
de 32 tests d'identité, de capture et de réutilisation des lectures passe aussi.
Le manifeste de sources et de références est `docs/gelano-sources-2026-11-08.json`.

## Application

Fermer Forgely puis relancer `OUVRIR FORGELY.bat`. Les sources et les références
locales sont modifiées ; aucun binaire ni changement distant n'a été publié.
Les objectifs de l'ancien équipement ne sont plus transférés au nouveau :
choisir le jet cible du nouvel objet pour obtenir les conseils correspondants.

## Autres moteurs examinés

RapidOCR et PaddleOCR sont des composants OCR ouverts sous Apache 2.0, pouvant
servir à un comparatif de lecture de nombres. Aucun remplacement n'a été
installé et aucune supériorité sur ces captures n'a été mesurée. Forge Saharash
est un atelier gratuit de simulation/apprentissage, sans démonstration trouvée
d'un moteur visuel réutilisable supérieur.

- [RapidOCR](https://github.com/RapidAI/RapidOCR)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Forge Saharash](https://forge.saharash.fr/)
