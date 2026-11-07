# Identification du nom accélérée — v22.05

## Causes observées dans le code

Le traitement de l'identité était placé après `read_atelier`, incluant l'historique, les effets, les reprises de lignes, les runes et le reliquat. Une identité pourtant visible attendait donc une lecture complète de plusieurs secondes. Les trois confirmations d'icône précédaient les trois confirmations de nom : la première confirmation du nom n'arrivait qu'à la troisième lecture, soit cinq cycles pour activer l'objet.

La recherche de suffixe normalisait aussi les 20 941 noms du catalogue à chaque essai. Sur le même environnement local, un fragment OCR non reconnu prenait environ 74,5 ms ; après mise en cache des noms normalisés, la médiane chaude mesurée sur 50 essais est de 0,93 ms. La première normalisation reste nécessaire une fois. Cette mesure ne représente pas le temps total d'identification sur le PC Windows.

## Correction

Un lecteur d'identité indépendant suit les dernières captures, contrôle la structure de l'atelier, extrait l'icône actuelle, lit les deux traitements du nom actif et les bornes Min/Max visibles. Il ne lance pas de lecture des runes, de l'historique des tentatives ni de balayage des caractéristiques manquantes. Les textes sont réutilisés uniquement sur pixels exactement identiques.

Les validations de l'icône et du nom avancent maintenant ensemble. L'activation exige toujours trois captures distinctes avec preuves concordantes. Les compteurs utilisent le compte, la génération, la fenêtre et l'identifiant de capture pour ne compter chaque image qu'une fois. Une lecture complète de la même capture peut toutefois enrichir une lecture rapide incomplète. Une lecture rapide sans nom ni correspondance d'icône ne consomme pas les confirmations du lecteur complet. Un nom illisible est retenté après une seconde même si ses pixels restent identiques. Les noms historiques ne deviennent pas une preuve d'identité actuelle. Un profil naturel incompatible reste un veto.

Le lecteur complet reste disponible en secours si les ancrages visuels du lecteur rapide ne correspondent pas à l'interface. Un atelier ou une icône illisible ne devient jamais un nom inventé. Une identité déjà vérifiée n'est pas réenregistrée à chaque capture tant que son icône, sa signature et son nom restent compatibles.

Une absence d'icône confirmée efface l'ancienne lecture et le puits : le compteur de ratés était remis à zéro avant que l'interface puisse constater l'absence. Ce cas dispose maintenant d'un état explicite, pour éviter qu'une identification plus rapide réutilise les données de l'objet précédent.

## Mesure et validation

La durée du nouveau lecteur apparaît sous `identification_objet` dans les performances rapides. `RETARD IDENTIFICATION OBJET` est séparé de `RETARD DERNIÈRE OBSERVATION` : une identification rapide ne masque pas un jet encore lent à lire.

Les régressions couvrent la lecture indépendante, le cache exact, l'invalidation des pixels, les captures dupliquées, les changements de génération et l'absence d'icône. Un test Tk vérifie l'activation à la troisième capture, puis l'effacement des anciens jets après disparition de l'icône. Les tests de compte, d'événements et de budget restent applicables.

Le délai réel sur la fenêtre DOFUS de l'utilisateur reste à mesurer ; aucun délai universel inférieur à une seconde n'est affirmé. Une image illisible ou un objet sans preuve de nom peut toujours demander une lecture supplémentaire.


La reprise d'un nom illisible déclenche une nouvelle capture sur image statique, sans attendre la cadence de sécurité de douze secondes. Les demandes restent espacées d'une seconde. Une reconnaissance rapide sans nom ni icône reconnue laisse la place au lecteur complet. Le lecteur rapide ne crée aucune observation de rune et ne remplit aucune caractéristique avec des valeurs théoriques.

Validation locale : 426 tests réussis, 16 ignorés (10 tests Tk réservés à l'environnement graphique et 6 captures absentes), 25 sous-tests. La relecture indépendante a identifié le risque de blocage du secours par une première lecture rapide ratée ; les tests de reproduction échouaient avant correction puis passent après correction. Le contrôle natif Tk vérifie trois captures, puis l'effacement du précédent jet à la disparition de l'icône.
