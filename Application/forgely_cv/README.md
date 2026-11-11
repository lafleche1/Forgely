# Vision classique pour Forgely — première version

Package autonome : **MSS, NumPy et OpenCV uniquement**. Aucun Tesseract,
EasyOCR, PaddleOCR ou VLM n'est chargé par cette chaîne. Le lecteur existant
de l'application Forgely n'est pas remplacé par ce prototype.

## Lecture numérique ajoutée

Voir [NUMERIQUE.md](NUMERIQUE.md) pour les valeurs actuelles, le puits décimal,
les profils de démonstration et leurs limites. La lecture se charge avec
`--numbers` ; elle ne remplace pas automatiquement le lecteur de Forgely.

## Installation et lancement

Depuis le dossier `Application`, utiliser le Python de Forgely :

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements-vision.txt
..\.venv\Scripts\python.exe -m forgely_cv --help
```

Les dépendances ont aussi été installées dans l'environnement local du projet.
La distribution OpenCV est `headless` : pas de fenêtre `imshow`, aucune dépendance
à une interface graphique supplémentaire. Les images de diagnostic sont des PNG.

## 1. Calibrer une vraie interface

Préparer une capture PNG du jeu à sa résolution physique. Choisir une petite
ancre distinctive et immobile : titre, icône de marteau ou partie stable du
bouton Fusionner. Éviter les états survolé/désactivé du bouton ; s'ils changent,
le template doit être recalibré. Aucune référence artificielle de DOFUS n'est
livrée : une image générique donnerait une fausse impression de détection.

```powershell
# EXEMPLE DE COORDONNÉES : à remplacer par celles de votre capture.
..\.venv\Scripts\python.exe -m forgely_cv calibrate `
  --image capture.png --game 0 0 1648 928 `
  --anchor 550 140 150 28 --stats 470 250 500 490 `
  --chat 277 247 199 482 --scale-tag "1080p-DPI100-interface100" `
  --output profil_dofus
```

Les quatre rectangles utilisent **X Y LARGEUR HAUTEUR dans la capture**.
L'ancre localise ensuite le jeu grâce au décalage et aux dimensions calibrés.
Un bouton seul ne révèle pas les limites de la fenêtre entière. Une fenêtre
partiellement hors de la zone capturée est rejetée, plutôt que rognée.

La police de DOFUS n'est pas garantie identique au pixel près pour tous les
joueurs : résolution, DPI, zoom d'interface, rendu et anticrénelage comptent.
Créer un profil et un dictionnaire de glyphes par configuration. Aucun étirement
automatique des glyphes n'est appliqué.

## 2. Capturer et masquer le chat

```powershell
..\.venv\Scripts\python.exe -m forgely_cv run `
  --profile profil_dofus/profile.json --monitor 1 --fps 60 --frames 300 `
  --debug-dir diagnostic_cv
```

Pour limiter le coût, ajouter `--region X Y W H` avec les coordonnées écran
physiques d'une région contenant toute la fenêtre. Les origines négatives des
moniteurs à gauche du principal sont prises en charge. Le premier repérage
cherche dans la capture entière ; le suivi recherche autour de l'ancienne ancre,
puis élargit la recherche s'il la perd. Deux ancres distinctes reconnues dans la
zone recherchée rendent la détection ambiguë. Le suivi local ne garantit pas
l'absence d'un second atelier hors de cette zone : limiter la capture à un seul
compte DOFUS pour cette V1.

`hsv.json` contient des plages **initiales à ajuster sur vos pixels**, pas des
couleurs universelles certifiées du jeu. H va de 0 à 179, S/V de 0 à 255.
Le rouge utilise deux intervalles. Les masques sont monochromes : fond 0,
glyphes retenus 255. Aucune érosion susceptible d'effacer les `−`, points ou
virgules n'est appliquée. Une icône ou un morceau de décor de même couleur peut
rester : le masquage couleur ne sait pas distinguer du texte d'une icône.

**Vert/rouge/bleu ne suffisent pas à certifier SC/SN/EC.** Une couleur peut
décrire une variation de caractéristique. Cette brique n'enregistre aucune
tentative, ne modifie aucun puits et ne nourrit pas l'apprentissage de Forgely.

MSS capture ce qui est affiché : une fenêtre recouvrant le jeu apparaît dans
l'image ; le jeu masqué ou minimisé n'est pas reconstruit. La présence d'une
ancre visible n'exclut pas une infobulle sur les statistiques. La certification
des valeurs et l'exclusion des occultations restent à ajouter avant intégration
au calcul du puits.

## 3. Constituer le dictionnaire local

```powershell
..\.venv\Scripts\python.exe -m forgely_cv glyph-samples `
  --mask diagnostic_cv/green.png --output police_a_etiqueter
```

Étiqueter manuellement les caractères extraits dans `a-etiqueter.json`, retirer
les icônes et composants incorrects, puis enregistrer la sélection sous
`manifest.json`. Exemple de format (images réelles à fournir) :

```json
{"glyphs": [
  {"char": "0", "file": "U+0030-0.png"},
  {"char": "-", "file": "U+002D-0.png"},
  {"char": "+", "file": "U+002B-0.png"},
  {"char": "é", "file": "U+00E9-0.png"}
]}
```

Utiliser fond noir/glyphe blanc, inclure chiffres, lettres, accents, `%`, points,
virgules et signes nécessaires. Plusieurs exemples du même caractère sont
acceptés. Les noms Unicode évitent les collisions entre majuscules/minuscules
sur Windows. Le dossier `font_dofus` fourni est volontairement vide.

Ajouter `--font police_a_etiqueter` au lancement pour activer `GlyphReader`.
L'API `reader.read(mask)` retourne `(texte, correspondances, lecture_acceptee)`.
Un glyphe absent ou ambigu devient `?` ; un masque vide n'est pas une lecture
acceptée. Il n'y a aucune correction automatique d'un inconnu en `0`.

Les caractères qui se touchent, les espaces, les accents détachés et les lignes
très proches demandent encore une calibration. Le découpage par contours reste
une première version, pas un lecteur numérique certifié.

## 4. Mesurer les performances

```powershell
..\.venv\Scripts\python.exe -m forgely_cv benchmark `
  --profile profil_dofus/profile.json --image capture.png --iterations 200
```

Ce benchmark mesure **le traitement seul**, après préchauffage. `run` mesure aussi
la capture, le délai capture-vers-résultat et le FPS réellement observé. Les
résultats indiquent p50/p95/p99 et si le p95 de capture-vers-résultat est inférieur
à 5 ms. Cela n'inclut pas la latence du rendu DOFUS, l'attente du prochain frame,
la certification temporelle, ni la présentation finale dans Forgely.

Première mesure locale : capture MSS 320×180 au p95 **7,60 ms** ; traitement
synthétique 800×480 avec suivi local, sans lecture de glyphes, au p95 **0,40 ms**.
Ce sont deux mesures distinctes, pas une mesure de reconnaissance en jeu.
La cible globale de 5 ms n'est **pas atteinte** par ce backend sur cette machine.
Les détails et limites figurent dans `BENCHMARK.json`.

**60 FPS est une consigne, 5 ms est une cible à vérifier.** Une acquisition
globale sur un grand écran, les recherches de template, le chargement CPU et
la taille des dictionnaires peuvent dépasser ces budgets. À 30 FPS, l'attente
entre captures peut déjà atteindre environ 33 ms : elle est distincte du temps
de traitement d'une image. Ne pas assimiler 5 ms de traitement à une réaction
garantie en 5 ms après l'apparition d'une rune.

## Modules

| Fichier | Rôle |
|---|---|
| `capture.py` | Session MSS persistante, cadence sans backlog, pixels physiques |
| `geometry.py` | Rectangles contrôlés et profil de calibration |
| `detection.py` | `matchTemplate`, score, ambiguïté et coordonnées absolues |
| `masking.py` | Conversion BGR → HSV et masques binaires |
| `glyphs.py` | Contours, regroupement, XOR matriciel et rejet de l'inconnu |
| `pipeline.py` | Analyse d'un frame, sans état de forgemagie |
| `__main__.py` | Calibration, exécution, exports et mesures |
