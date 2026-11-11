# Reprise locale dans Work — 10 novembre 2026

## Point de reprise vérifié

Le chat référencé `6af38134-62fc-83ed-a176-ab2ac7f06c1d` ne contient que la
demande de reprise. L'état exploitable vient donc des fichiers locaux, notamment
`REPRISE_OCR_2026-11-10.md`, du plan `2026-11-10-numeric-worker.md`, des sources
modifiées à 21:35 et du benchmark concurrent enregistré à 21:37.

Le lecteur numérique indépendant était déjà intégré et activé dans les sources,
alors que le dernier paragraphe du compte rendu décrivait encore le prototype.
Cette intégration a été conservée. Aucun téléchargement ni remplacement depuis
une ancienne version n'a été réalisé. Le dossier n'a pas de métadonnées Git.

## Correction ajoutée pendant cette reprise

Dans `forgely.py`, `numeric_worker` consommait la demande de relecture du puits
avant l'OCR. Si l'atelier était masqué ou si l'OCR levait une exception, la
capture suivante ne portait plus le jeton imposant une nouvelle lecture.

La demande est désormais rétablie si aucune mesure numérique n'a été publiée,
uniquement si la session est encore active et de même génération. Une lecture
valide consomme la demande ; une nouvelle demande arrivée pendant cette lecture
reste présente. Les protections d'identité, de provenance et de stabilité restent
en place. Aucun résultat de rune ni chiffre absent n'est déduit.

Trois cas ajoutés à `Tests/test_numeric_worker.py` : masque, erreur OCR et puits
absent. Avant correction : deux échecs reproduits, le troisième cas passait déjà.
Après correction : dix tests passent dans ce fichier et celui de relecture après
rune. Une relecture du correctif n'a trouvé aucun problème bloquant.

Sauvegardes avant édition : `.tmp/reprise-before/forgely.py`,
`.tmp/reprise-before/test_numeric_worker.py` et `hashes.json`.

## Vérifications des corrections existantes

- Identification sur les captures réelles disponibles et rejet des bornes
  contradictoires ; conservation de l'identité pendant une lecture masquée.
- Lecture de l'intelligence et des autres statistiques, y compris ligne
  sélectionnée, zéro PA, signes, valeurs hors maxima et profils de tailles variées.
- Synchronisation des cibles entre les éditeurs, persistance des zéros et refus
  d'un éditeur devenu obsolète.
- Comparaison simple/Pa/Ra, Pa Vi et Pa caractéristiques de réserve ; Ra prises
  en compte dès 10 de puits lorsque les autres gardes autorisent la candidate.
  Ce seuil n'impose pas systématiquement une Ra et ne prouve pas son optimalité.
- Actualisations tardives, portée du contrôle de fraîcheur numérique, caches,
  continuité et publication indépendante de l'historique.

Les premières vérifications ciblées ont donné 193 réussites et une exclusion.
Suite complète finale sur les sources corrigées : **2297 tests réussis,
27 ignorés et 42 sous-tests réussis**, en 216,93 s ; code de sortie zéro.
Compilation des deux fichiers Python modifiés réussie. Journal :
`.test-tmp/reprise-final.log`. Les ensembles se recoupent et ne s'additionnent pas.

## Limites et lancement

Le premier lancement global rencontrait des refus d'accès au dossier temporaire
Windows. Avec un dossier temporaire local, un seul échec subsistait : un ancien
test appelle directement Tesseract sans sa découverte automatique. Tesseract est
installé dans `C:/Program Files/Tesseract-OCR` ; le lancement final ajoute ce
répertoire au PATH de son seul processus et utilise un dossier temporaire local.
Aucun paramètre système n'est modifié.

Le benchmark concurrent déjà présent indique une médiane numérique de 912,28 ms
pour le chemin commun contre 861,55 ms pour le chemin indépendant, sur cinq
comparaisons de la capture Kido fixe avec historique actif. Ces mesures antérieures
n'ont pas été refaites pendant cette reprise et ne mesurent ni capture live ni GUI.

La latence réelle dans DOFUS et l'optimalité du conseil ne sont pas démontrées par
les tests. Les probabilités provisoires et les pertes inconnues ne sont pas
transformées en certitudes. Aucun exécutable n'a été reconstruit, aucune application
en cours n'a été redémarrée. `OUVRIR FORGELY.bat` lance bien ces sources locales.
