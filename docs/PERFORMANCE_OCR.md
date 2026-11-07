# Réactivité et OCR — optimisation du 7 novembre 2026

## Changements

- L'OCR partage les requêtes simultanées ayant exactement les mêmes pixels et
  paramètres. Les résultats réussis sont conservés au plus deux secondes, dans un
  cache limité à 64 entrées. Les erreurs restent réessayables. Le mode titre,
  les langues, la palette et la configuration restent distincts ; seule la
  métadonnée de diagnostic `forgely_preview_zone` est ignorée.
- La recherche de l'exécutable et des modèles est réutilisée pendant cinq secondes.
- Les processus Tesseract héritent par défaut de `OMP_THREAD_LIMIT=1`, pour éviter
  la concurrence excessive entre leurs threads. Une valeur explicite dans
  l'environnement est conservée. Aucun modèle, langue ou mode PSM n'est simplifié.
- La récupération de lignes d'effets réutilise seulement une image et un jet
  d'entrée identiques, pendant huit secondes maximum, dans quatre entrées. Un
  changement de pixel, de valeur déjà lue, ou une erreur impose une nouvelle lecture.
  Le masque de texte vert utilise les opérations natives Pillow, avec les mêmes
  seuils de couleur.
- Les préférences et le catalogue d'icônes utilisent des caches bornés et invalidés
  par l'identité/taille/dates du fichier. Les dépenses restent lues dans la base,
  y compris les actions sans rune ou objet identifié.
- Les titres DOFUS versionnés évitent une ouverture de processus Windows inutile.
  La géométrie et la présence des fenêtres restent relues à chaque capture.
- MSS est réutilisé par thread ; la conversion BGRA/RGB passe directement par
  Pillow. Les ressources du thread sont fermées à son arrêt ou sur erreur.
- La détection de changement couvre désormais tout le panneau de runes et toutes
  les lignes d'effets. Une modification isolée n'attend plus le rafraîchissement
  périodique de douze secondes.
- Le traitement de l'interface passe de 200 à 40 ms entre deux passages au repos.
  Une file chargée reprend après 1 ms, avec au plus 64 messages et environ 8 ms de
  traitement par passage. L'observateur ne dort plus 100 ms après chaque lecture.

## Isolation des sessions et conservation des événements

Une capture est liée à son compte et à une génération de session. Si le contexte
change pendant une lecture, les résultats en cours sont écartés ; un ancien
observateur ne peut pas réinitialiser les données de son remplaçant.

Une tentative déjà acceptée reçoit un reçu immuable avant son insertion dans la
file. Son identité provient uniquement d'un contexte d'objet confirmé auparavant,
avec icône et profil compatibles, jamais du nom courant au moment de l'affichage.
Le reçu reste enregistrable si le joueur change de compte ou arrête l'observation
avant son affichage. Une identité non confirmée conserve la tentative à part,
sans inventer une attribution ni alimenter les statistiques d'un autre objet.

## Mesures locales

Mesures sur l'hôte Linux de développement ; ces nombres ne sont pas des mesures
de bout en bout dans le jeu sous Windows. Le fichier de référence utilisé est
`Tests/fixtures/effects_vitalite_342.png` (442 × 680).

| Opération | Avant | Après | Méthode |
| --- | ---: | ---: | --- |
| Cinq OCR identiques du fichier de référence | 2,299 s | 0,380 s | Vrai Tesseract, mêmes sorties, une reconnaissance au lieu de cinq |
| OCR non mis en cache | 470,0 ms | 418,5 ms | Médiane de cinq processus frais par réglage OpenMP |
| Deux OCR simultanés non mis en cache | 753,5 ms | 423,4 ms | Médiane du dernier résultat de trois paires ; sorties identiques sur les 22 essais séquentiels/parallèles |
| Masque vert du fichier de référence | 19,494 ms | 3,128 ms | Même résultat pixel par pixel ; mesure sur trente appels |
| Conversion BGRA/RGB, 1920 × 1080 | 11,049 ms | 4,758 ms | Médiane de vingt captures MSS synthétiques, même résultat RGB |
| Détection visuelle complète, 1920 × 1080 | 3,676 ms | 3,414 ms | Médiane de soixante appels, zones couvertes plus nombreuses après correction |
| Recherche d'une icône déjà utilisée | 192,9 µs | 15,3 µs | Cache chaud, meilleur de trois lots de 3 000 appels |
| Lecture des préférences avec prix renseignés | 41,2 µs | 21,5 µs | Même protocole de cache chaud |

Un test déterministe sur trente images partielles identiques réduit les appels
OCR de récupération de 540 à 18. Ce comptage emploie un moteur simulé pour
isoler les appels évités ; il ne constitue pas un chronométrage du jeu.

Une nouvelle image nécessite toujours une vraie reconnaissance. Les bénéfices des
caches dépendent donc de la stabilité des zones, de la résolution et des modèles
installés. Une interface différente de la capture de référence nécessite toujours
de vérifier les zones de lecture.

## Vérification et reproduction

Les régressions couvrent concurrence, expiration et bornes des caches, changement
de pixel/configuration, panne OCR puis reprise, fichiers remplacés, comptes et
sessions changés, conservation des reçus et absence de double enregistrement.

```sh
python -m pytest -q
python -m compileall -q Application
```

Tests concernés : `tests/test_ocr_backend_performance.py`,
`Tests/test_ocr_regions_performance.py`, `tests/test_ui_data_performance.py`,
`tests/test_window_discovery_performance.py`,
`Application/tests/test_pipeline_performance.py`.

Pour mesurer le gain réel, relever dans les diagnostics les médianes et p95 de
capture, OCR, cycle complet et retard d'affichage, sur le même atelier, avec les
mêmes réglages DOFUS et les mêmes actions, avant/après. Ne pas déduire un délai
global en additionnant les gains de microbenchmarks réalisés séparément.

Documentation primaire consultée :
[MSS, réutilisation des instances](https://python-mss.readthedocs.io/latest/usage.html),
[MSS, conversion BGRA](https://python-mss.readthedocs.io/latest/examples.html),
[Tesseract, FAQ sur les threads](https://github.com/tesseract-ocr/tessdoc/blob/main/FAQ.md).
