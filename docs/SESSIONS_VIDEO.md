# Apprendre de sessions MP4

Ouvrir **Entrainement_Forgely.exe**, puis l’onglet **Sessions vidéo**.

1. Ajouter les MP4 depuis le PC et choisir une vidéo dans la liste.
2. Vérifier l’aperçu. Si nécessaire, choisir puis tracer chacune des cinq zones : nom de l’objet, caractéristiques, rune utilisée, journal et puits. Mémoriser la disposition pour les prochaines vidéos.
3. Si le nom de l’objet est illisible, utiliser « Confirmer un objet illisible » uniquement si tous les passages concernés montrent cet objet. Les caractéristiques manquantes restent inconnues.
4. Lancer « Analyser / reprendre ». L’arrêt sauvegarde la progression ; la reprise réutilise les lectures compatibles et conserve les corrections.
5. Choisir une tentative pour comparer les images avant/après. Corriger les valeurs visibles ou rejeter la lecture. Une case vide signifie inconnue. Plusieurs tentatives entre deux lectures, une coupe ou des preuves manquantes restent exclues.
6. Consulter le rapport puis « Transmettre à Forgely ». Seules les observations qualifiées contribuent à la calibration. Retransmettre après correction ou rejet remplace les contributions précédentes de cette vidéo.

## Ce que l’outil mesure

Objet, rune, SC/SN/EC explicitement lus dans le journal, jets et puits avant/après, consommation et pertes des tentatives admissibles. Le rapport détaille les effectifs par objet/rune/contexte et leurs incertitudes. Le classement « cohérent » signifie que les contrôles visuels et comptables sont satisfaits ; il ne certifie pas ce que le serveur a réellement exécuté.

Le SC conserve le puits. Un over n’est pas déjà du puits. Une ligne absente n’est pas assimilée à zéro. Une vidéo n’est pas un ensemble de simulations et n’active pas automatiquement une stratégie.

## Limites

**Images uniquement : aucun traitement audio.** Aucun envoi des vidéos sur Internet et aucun clic dans le jeu.

Le journal doit afficher des résultats explicites et un décalage de lignes reconnaissable. Un journal affichant seulement des variations de caractéristiques ne suffit pas à attribuer SC/SN/EC. Une vidéo accélérée, des tentatives très rapprochées, des lignes masquées, une compression forte ou des coupes peuvent produire un rapport partiel. L’échantillonnage ne garantit pas l’exhaustivité.

Les fichiers originaux restent en place. Les images de preuve et lectures sont conservées dans `Entrainements/Videos` ; une longue vidéo peut produire beaucoup d’images. Les changements de disposition/lecteur créent une nouvelle analyse, l’ancienne étant archivée. L’empreinte du contenu évite les doublons quand on déplace ou réimporte la même vidéo. Les exports de deux montages différents d’une même session ne sont pas automatiquement reconnus comme doublons.

Le moteur de lecture s’appuie sur OpenCV, Pillow et Tesseract déjà utilisés localement. Si une installation ne possède pas OpenCV, utiliser les dépendances de vision du projet. Les essais automatisés et le MP4 synthétique avec OCR valident la chaîne technique ; une vraie session annotée reste nécessaire pour mesurer la reconnaissance en jeu.

## Raisonnement et entraînement

Le conseiller explique maintenant la valeur actuelle, la cible, le gain et le poids de la rune, la valeur projetée et la couverture théorique du puits. Il distingue cible utilisateur et maximum naturel. Il affiche aussi les options préparatoires limitées à comparer, sans prétendre qu’elles sont optimales.

Dans **Sessions virtuelles**, l’option **Comparer les actions préparatoires / overs temporaires** permet à l’apprentissage par objet d’explorer des petites poses sur des lignes déjà à cible. La réserve de puits ne change que selon le résultat simulé ; aucun bonus ne récompense la fabrication de puits. Le critère reste le jet complet. Les états distinguent exactement les surplus.

Ce mode est expérimental, désactivé par défaut car les premiers essais n’ont pas montré de gain global. Il ne se combine pas encore avec la recherche de stratégie généralisable. Ses politiques sont sauvegardées séparément et restent exclues des conseils actifs tant que la sélection en direct ne possède pas une validation adaptée. Les apprentissages classiques et archives sont conservés.

Les observations vidéo qualifiées calibrent les estimations réelles utilisées par le conseiller. L’entraînement virtuel conserve son modèle de simulation identifié ; il n’est pas présenté comme un apprentissage des probabilités exactes du serveur à partir d’une seule vidéo.
