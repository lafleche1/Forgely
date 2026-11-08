# Lecture numérique locale

`numbers.py` lit les valeurs actuelles et le puits sans Tesseract, EasyOCR,
PaddleOCR ou VLM. Il ne remplace pas automatiquement l'ancien lecteur de
Forgely et ne modifie ni les observations, ni le puits métier, ni l'apprentissage.

## Essayer les profils de démonstration

Depuis `Application` :

```powershell
..\.venv\Scripts\python.exe -m forgely_cv read-numbers `
  --image ..\Tests\fixtures\cv_gelano_effects.png `
  --numbers forgely_cv\profiles\gelano --iterations 200

..\.venv\Scripts\python.exe -m forgely_cv read-numbers `
  --image ..\Tests\fixtures\effects_vitalite_342.png `
  --numbers forgely_cv\profiles\cycloide --iterations 200
```

| Profil | Valeurs vérifiées visuellement |
|---|---|
| Gélano, crop 438×651 | Vitalité 10, PA 0, puits 0 |
| Cycloïde, crop 442×680 | 11 caractéristiques, dont Vitalité 342 et Tacle 0 ; puits 0,1 |

**Ces images ont servi à construire les références : leur relecture est un
contrôle de calibration, pas une validation indépendante de fiabilité.** Un
test recomposant 24 à partir de glyphes réels vérifie aussi que le code lit les
pixels nouveaux ; cette recomposition n'est pas une nouvelle capture en jeu.

Les dictionnaires sont partiels : Gélano contient les formes de 0 et 1 ;
Cycloïde contient 0 à 8 et la virgule. Le 9 et les signes doivent être ajoutés
depuis d'autres exemples réels. Aucun caractère manquant n'est inventé.

## Garanties de traitement et limites

- Chaque champ comporte une ROI de **valeur actuelle seulement**, sans icône,
  Min/Max ou Modif, et une ROI de garde sur son libellé.
- Si le libellé change, le nombre n'est pas associé à l'ancienne statistique.
- Les glyphes sont comparés à leur taille native, par XOR. Le matching numérique
  est exact par défaut : un rendu différent peut donc être refusé.
- Le puits utilise `Decimal` et est exporté comme chaîne décimale exacte.
- Un inconnu, un signe ambigu, un puits négatif, un espacement anormal ou des
  dimensions incompatibles entraîne un rejet. `01` n'est pas corrigé en `1` :
  une virgule aurait pu disparaître. Une absence ne devient jamais zéro.
- `accepted` couvre uniquement les champs configurés. Cela ne prouve pas que
  toutes les lignes de l'objet ont été configurées ou que son identité est bonne.
- Les gardes ne remplacent pas le contrôle de l'objet et des occultations.
  DPI, zoom, anticrénelage et couleur peuvent nécessiter une nouvelle calibration.

## Créer une calibration

Utiliser `profiles/*-annotations.json` comme modèle. Les rectangles `X Y W H`
sont relatifs à l'image passée à la commande. `box` contient le nombre actuel,
`guard_box` un libellé stable ; `kind` vaut `stat` ou `pool` et `text` est une
transcription **manuellement vérifiée**. Le mode `bright` convient au texte
clair sur fond sombre ; `white` peut isoler le texte blanc d'un badge coloré.

```powershell
..\.venv\Scripts\python.exe -m forgely_cv calibrate-numbers `
  --image mon_crop.png --annotations mes_annotations.json --output nouveau_profil
```

Le tableau facultatif `samples` peut ajouter des exemples :
`{"box":[20,20,20,20],"text":"-2","mode":"white"}`. Les coordonnées sont à
remplacer. Vérifier le découpage avant de réutiliser le profil : un étiquetage
erroné pourrait créer de mauvaises lectures. Le nombre de composants doit
correspondre au nombre de caractères transcrits.

Les valeurs attendues par champ ne sont pas stockées dans le profil d'inférence :
il contient seulement les noms, positions, gardes et formes étiquetées des
caractères. Un profil existant n'est pas écrasé : choisir un nouveau dossier.

## Intégration à la capture V1

Ajouter `--numbers nouveau_profil` à `run` ou `benchmark`. Ce profil doit être
calibré sur le **crop stats exact** du profil d'interface ; inclure le puits
dans ce crop si son champ y est défini. Aucune mise à l'échelle n'est appliquée.

L'API `VisionPipeline.process()` expose `result.numbers`. `run` confirme les
nombres après trois captures distinctes concordantes dans une fenêtre fraîche
d'une seconde. Inconnu, perte de détection, changement de contexte, frame
périmé ou variation des valeurs annulent la confirmation. Répéter le même
identifiant de frame ne compte jamais plusieurs fois.

Le JSON fournit `jet`, `pool`, le détail des champs, `accepted` et
`temporal_confirmation`. `read-numbers` traite une seule image : sa confirmation
temporelle reste fausse. La stabilisation ne garantit pas l'identité de l'objet.

## Mesures

Lecture numérique seule, 200 répétitions des crops de calibration :
Gélano médiane 0,21 ms / p95 0,44 ms ; Cycloïde médiane 1,19 ms / p95 1,98 ms.
Une autre exécution CLI du Cycloïde a donné p95 2,50 ms. Ces mesures excluent
capture, localisation, attente des frames et affichage ; elles ne prouvent pas
une latence globale sous 5 ms.

Avant remplacement de Tesseract dans Forgely : compléter les caractères et
tester des captures différentes de celles de calibration, des valeurs modifiées,
d'autres objets, échelles, occultations et séparateurs décimaux. Mesurer le jet
complet et le puits exact plutôt que seulement la vitesse.
