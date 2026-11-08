# Forgely 22.16 — réunion des travaux PC et GitHub

## Périmètre

Base distante : `f3d94809126a6d452c028e8ac72d63b312dca3e4`.
La copie PC 22.15 contenait déjà la vision numérique, les objectifs mesurés,
le sélecteur d'équipement, la matrice prédictive, l'expérience incrémentale,
les simulations locales et l'entraîneur. Ces sources sont conservées.

Les cinq commits GitHub postérieurs au protocole partagé `1c652809` sont pris
en compte : modèle vidéo, précision du contexte et niveau, simulateur dynamique,
banque de pertes qualifiées, bilans de session et optimisations de réactivité.
L'identification rapide indépendante, déjà présente dans l'historique distant
mais absente de cette copie PC, est également raccordée.

## Résolution des divergences

- L'OCR conserve les signes, les zéros contextualisés, les lectures par pages,
  la confirmation des lignes et les contrôles de changement d'objet du PC.
  Le travail d'identification peut maintenant arriver avant l'OCR complet ; une
  même capture enrichie ne compte pas comme deux confirmations.
- Les noms enregistrés et les bornes CSV sont indexés ; le catalogue local de
  bornes reste prioritaire comme base et les imports utilisateur le complètent.
  Les analyses de texte, statistiques groupées, icônes et libellés évitent le
  travail répétitif ; la capture vise sa période en tenant compte du temps passé.
- La matrice PC et ses politiques restent disponibles. Les fonctions `estimate`
  et `calibrate` du modèle vidéo coexistent dans `forgely_predictive.py` avec
  l'API matricielle. Une preuve simulée déjà utilisée n'est pas multipliée une
  seconde fois par le modèle vidéo. Les pourcentages sont des estimations
  explicitement attribuées, jamais des taux officiels ni une chance de jet final.
- La calibration vidéo emploie seulement les transitions complètes dont la
  comptabilité est cohérente : au moins 30 résultats réels comparables et un
  prior de 200. Les anciens OCR partiels ne sont pas promus en données qualifiées.
  Les EC inchangés et SN avec perte du gain nominal peuvent être qualifiés.
- L'expérience PC continue à être mise à jour par curseur. Les bilans relient
  une prévision antérieure au résultat à l'observation et au contexte exact.
  Les objectifs mesurés courants remplacent un ancien plan dans les bilans et
  le simulateur ; aucun ancien objectif ne doit réapparaître silencieusement.
- Le simulateur dynamique est accessible dans les outils, avec arrêt sur perte
  inconnue par défaut et approximation explicite facultative. Les simulations
  ne deviennent jamais des observations réelles.
- Choix explicite de l'utilisateur : budget atteint = alerte, conseils maintenus
  par défaut. La suspension est une option. Le budget du simulateur est explicite
  et l'entraîneur PC garde son objectif de jet sans contrainte économique.
- Le cache global de conseils distant n'est pas réutilisé dans cette fusion :
  les objectifs mesurés, l'expérience et les simulations du PC ajoutent des
  dépendances. Les conseils sont recalculés ; les autres caches bornés sont gardés.
  Ce choix applique la solution de repli prévue dans la conception validée.

## Protection des données et distribution

Une sauvegarde des sources locales et un inventaire SHA-256 précèdent la fusion.
Le report local exige que les fichiers d'origine n'aient pas changé entre-temps.
Aucune suppression de dossier n'est autorisée sans l'accord ultérieur du joueur.
Les captures privées de tests restent locales ; les tests concernés sont ignorés
explicitement lorsqu'elles ne sont pas fournies. Les données personnelles,
environnements Python et historiques d'entraînement locaux restent en place.

Cette mise à jour concerne les sources du copilote lancées par son lanceur Python.
L'exécutable autonome de l'entraîneur et l'ancienne archive de distribution ne
sont pas remplacés ou présentés comme une nouvelle compilation 22.16.
La publication se fait sur une branche dédiée avec proposition de fusion ; main
reste inchangée jusqu'à l'intégration de cette proposition.

## Validation

Copie PC avant fusion : 1543 tests réussis, 25 ignorés, 42 sous-tests réussis.
Après correction des deux défauts de revue (lien d'observation des transitions
différées et SN inchangés), la suite avec références privées locales donne
**1641 réussites, 25 exclusions et 42 sous-tests réussis**.
Une extraction propre des fichiers préparés pour GitHub, sans captures privées,
donne **1621 réussites, 46 exclusions et 42 sous-tests réussis**.
Contrôles Tk Windows isolés : **15 réussites** (tableau de bord, budget, objectifs
flottants, apprentissage et simulateur), puis **5 réussites et 10 sous-tests**
pour le sélecteur d'équipement. Compilation des sources réussie.

Un passage global avec tous les tests Tk a rencontré une erreur intermittente
d'accès à `ttk/fonts.tcl` au démarrage du second groupe de fenêtres ; les mêmes
groupes passent dans des processus isolés. Il n'est pas présenté comme une suite
globale graphique entièrement réussie.

L'association des résultats différés utilise la capture, la génération, le titre,
la frame d'événement, l'objet, la rune et le résultat ; un événement non associé
ne peut pas qualifier une prévision. Les tests reproduisent les deux défauts
avant correction et vérifient aussi le refus d'une frame différente.
Aucune mesure de latence de bout en bout ni de réussite dans DOFUS n'est revendiquée.

## Report local vérifié

La version 22.16 est installée dans le dossier principal après vérification des
empreintes d'origine : **438 fichiers installés, dont 356 fichiers existants
mis à jour et 82 ajouts ; aucun fichier supprimé**. Le total comprend des
normalisations de fins de ligne, pas 438 modifications fonctionnelles.
Les rapports et le manifeste détaillé sont fournis en complément.

Depuis le dossier principal après installation : **1641 tests réussis,
26 ignorés, 42 sous-tests réussis** ; compilation réussie. Tous les fichiers
installés ont été comparés à la copie de préparation validée.
Le nouveau test graphique de l'option de budget explique l'exclusion
supplémentaire dans la suite courante sans activation des tests Tk.

Voir [l'inventaire exact des fichiers](FICHIERS_FUSION_2026-11-08.json).
Les quatre anciens chemins `tests/` sont regroupés sous `Tests/`, avec conservation
des variantes de tests, pour éliminer les collisions de casse sous Windows.
