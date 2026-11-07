> **Vision produit actuelle :** Forgely est un assistant communautaire gratuit. Les statistiques seront mutualisées sur un serveur central lorsque celui-ci sera disponible. Voir [VISION_COMMUNAUTAIRE.md](VISION_COMMUNAUTAIRE.md). La version présente fonctionne encore localement.

## Version 0.19.7 — Laboratoire de validation externe

Ajout de `laboratoire_observations.py` et `forgely_validation.py` : audit des observations vérifiées, intervalles de confiance, exclusion des observations automatiques non revues et des simulations. Aucun ajout à l’interface joueur. Voir `README_LABORATOIRE.md`.

## Forgely 0.19.4 — Équipement automatique ou saisie de secours

L’équipement déjà enregistré est associé automatiquement uniquement si son nom est relu de manière stable par l’OCR (3 lectures identiques). Dans ce cas, le menu du logo ne propose plus de saisie manuelle. Si l’élément n’est pas reconnu, un clic droit sur le logo permet de choisir une fiche ou de saisir un nom. Aucun nouvel équipement n’est créé à partir d’un texte OCR non vérifié ; le jeu n’affiche pas toujours le nom de l’objet. Le suivi reste local.

## Forgely 0.19.3

- Logo flottant : point vert si l'atelier de FM est détecté, rouge sinon, gris si l'observateur est arrêté.

# Forgely — Historique des versions et notes

Ce correctif intègre **105 références d’icônes étiquetées depuis les captures que vous avez envoyées**, sans nécessiter d’importation sur Internet. Les 105 associations nom / image sont accessibles dans `catalogue_dofus3/index.json` et les fichiers PNG. Ce total ne certifie **pas** la couverture exhaustive de DOFUS 3, et les découpes restent à vérifier en conditions réelles.

## Installer
1. Décompressez l’archive dans un nouveau dossier.
2. Lancez `installer_windows.bat`, puis `demarrer_forgely.bat`.
3. Les références locales sont automatiquement chargées par Forgely. Ne cliquez pas sur « Importer catalogue DOFUS 3 » : cela servirait à solliciter l’API externe.
4. La position de la rune **dans l’atelier de forgemagie** doit encore être calibrée une fois. Sur une capture, cliquez le centre exact de l’icône à détecter, et testez la correspondance avec « Diagnostic OCR ».

## Précautions
- Un fichier avec rune et nom visible est une référence **étiquetée**, pas une reconnaissance prouvée en temps réel. La validation sur l’écran de l’atelier est encore nécessaire.
- Forgely refuse les icônes trop différentes et les correspondances ambiguës. Ne considérez pas ces images comme une garantie de reconnaissance automatique.
- Pas de mise en commun, aucune donnée envoyée en ligne par l’observateur local.
- Les noms / visuels proviennent des captures fournies par le joueur et ne sont pas destinés à être redistribués commercialement sans vérification des droits.
- Le catalogue n’est pas une base de probabilités. Les tests statistiques exigent des événements avec rune, jet et résultat fiables.
- Les anciennes observations restent dans `%LOCALAPPDATA%\Forgely\observations_locales.sqlite3`.

Voir `catalogue_dofus3/index.json` pour toutes les références, ainsi que l’archive indépendante `Forgely-Catalogue-105.zip` pour la planche et les fichiers CSV.

## Version 0.13 — Équipements accessibles depuis le logo flottant

- Depuis le **mode discret**, clic droit sur le logo → **Équipement actuel / choisir / créer**.
- Une fenêtre compacte permet de choisir une fiche, de donner un nom **uniquement si l'objet n'est pas reconnu**, ou de consulter son tableau.
- Une fiche unique par nom normalisé (casse, accents, espaces) : les statistiques sont stockées dans la base locale existante `%LOCALAPPDATA%\Forgely\observations_locales.sqlite3`.
- Chaque équipement dispose d'un tableau des tentatives SC/SN/EC, avec rune, date et source.
- Lorsqu'un équipement **déjà connu** apparaît distinctement dans la zone OCR de l'atelier pendant plusieurs captures, sa fiche est réutilisée. Si le nom est illisible, Forgely ne doit pas deviner le nom ni réattribuer une tentative à un objet reconnu auparavant.
- **Limitation importante** : la capture actuelle de la fenêtre de Joaillomagie ne montre pas systématiquement le nom de l'objet (parfois juste son icône et ses caractéristiques) ; il est donc impossible de promettre une identification automatique de *tous* les nouveaux équipements. Les objets non reconnus nécessitent une sélection ou une identification ponctuelle dans le menu du logo.
- Les nouveaux noms OCR incertains restent dans une file de candidats, hors statistiques. Aucune transmission réseau des observations.
- Les probabilités ne sont pas officielles : seules les fréquences des observations complètes sont calculées.

Sous Windows, ferme l'ancienne version, décompresse ce dossier, lance `installer_windows.bat` puis `demarrer_forgely.bat`. Les références d'icônes incluses dans 0.12.1 restent fournies. Les tests Python ne remplacent pas les tests de capture et d'interface sur DOFUS.


## Forgely 0.14 — Reconnaissance ciblée de l'interface

Cette version utilise **la capture de référence du joueur du 6 novembre 2026 (1648 × 928)** pour découper les zones `titre`, `historique`, `effets`, `colonnes Pa/Ra` et `reliquat`. Elle vérifie la présence du titre de métier avant toute lecture ; après trois absences consécutives, elle réinitialise l'historique afin d'éviter de compter les résultats déjà affichés. Le tableau de bord indique désormais le reliquat et les quelques caractéristiques **lues** (pas encore validées). Le diagnostic exporté contient ces zones séparées, sans copier tout l'écran.

### Limitations importantes avant d'exploiter les probabilités
- Les positions proviennent **d'une capture précise** : déplacer l'atelier, changer l'échelle ou la résolution peut invalider les régions OCR.
- Le champ `Pa`/`Ra` affiche notamment des **quantités**. Il ne prouve pas à lui seul quelle rune a été posée. Il faut encore détecter une sélection, une fusion et son résultat de façon synchronisée ; aucune attribution forcée n'est autorisée.
- L'identité des nouveaux objets (et certains jets) peut être absente ou illisible. Les tentatives ambiguës doivent rester hors des pourcentages.
- Le reliquat affiché peut être lu, mais le modèle complet du puits et le calcul d'une meilleure stratégie restent non validés en jeu.
- Un moteur de stratégie expérimental (`forgely_strategy.py`) existe, mais **il n'est pas branché en conseil autonome** : il n'y a ni taux officiels ni garantie de jet parfait.
- Les captures locales nécessaires pour étalonner d'autres configurations pourront être exportées avec « Exporter les zones OCR ».

### Installer
Fermer l'ancienne version, décompresser dans un dossier distinct, lancer `installer_windows.bat` puis `demarrer_forgely.bat`. Les statistiques existantes restent sous `%LOCALAPPDATA%\Forgely`. Exécuter `python -m unittest discover -s tests` pour les tests Python (hors validation graphique Windows).


## 0.15 — Données de référence et statistiques de probabilité

- `forgely_probabilites.py` documente les bonus et poids des runes connus, et laisse les inconnus à `None`.
- Le panneau « PROBABILITÉS PAR RUNE » montre les pourcentages *observés* SC/SN/EC par objet et par rune, avec le nombre d’essais.
- Le module calcule des intervalles de confiance Wilson à 95 % et signale les petits échantillons. Les nombres observés ne représentent pas encore des probabilités causales, car le jeu ne collecte pas de manière fiable le jet et le puits à chaque essai.
- Il n’existe pas de table officiellement publiée de taux fixes SC/SN/EC par rune. Aucun taux général fictif n’a été introduit.
- Un repère communautaire ≈1% SC est uniquement disponible pour les tentatives **exo** PA/PM explicitement identifiées (la détection exo n’est pas encore automatique) ; **non appliqué par défaut** et non confondu avec les résultats locaux.
- Sources de connaissance à vérifier selon la version du jeu : https://dofusfashionista.gg/fr/dofus2/forgemagie/ et https://www.millenium.org/guide/282643.html ; ces sources ne sont pas une formule officielle de DOFUS 3.
- Aucun envoi de données ni ajout d’automatisation des clics.
- Aucune modification des règles de collecte : les événements sans rune ou sans contexte fiables restent exclus.


## Version 0.16 — FM classique, over et exo généralisé

- `forgely_fm_model.py` distingue les caractéristiques naturelles (jusqu’au jet maximum connu), les overs (dépassement du maximum) et les exos (caractéristiques absentes du jet naturel), y compris Vita, résistances et dommages.
- Le moteur requiert **la fiche théorique vérifiée de chaque équipement** : le jet affiché à l'écran ne permet pas à lui seul de savoir si une caractéristique est exotique.
- Contrôle d'un budget de 101 de poids ajouté en exo/over **selon les guides communautaires DOFUS classiques**. Un poids inconnu bloque le verdict ; il n'est pas supposé nul. Vérifier la compatibilité exacte avec DOFUS 3 en jeu.
- Repère de succès critique d'environ 1 % seulement pour les exos **lourds** PA, PM, PO et invocation (non officiel, distinct du jeu réel). Tous les autres exos restent sans taux de base connu.
- `simulate_distribution()` effectue des essais *hypothétiques* à partir de probabilités fournies en entrée : aucun résultat simulé n'est ajouté aux statistiques réelles. Ce n'est ni une copie ni une rétro-ingénierie du moteur de DoFocus.
- Les chiffres de DoFocus ne sont pas importés : leur simulateur n'a pas été reproduit et ses règles ne sont pas garanties.
- Ce module est une **base de calcul**, pas encore un nouveau bouton d'interface ni une recommandation complètement automatisée.

Exécuter dans le dossier du programme : `python -m unittest discover -s tests` pour vérifier les fonctions.

Sources de référence, à recouper avec DOFUS 3 actuel : https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus ; https://www.tofus.fr/fiches/forgemagie ; https://www.eclypsia.com/home/dofus/guides/dofus-guide-forgemagie-72756.html


## Version 0.16.1 — Connaissances du guide Huzounet (30/09/2026)

Source : https://huzounet.fr/guides/forgemagie

- Nouveau module `forgely_huzounet.py` : classification du **jet proposé** en FM classique / over / exo, calcul explicite de reliquat à partir de pertes confirmées, indices de priorité qualitatifs et trois stratégies-types (concessions, puits, brisage).
- Dans `forgely_probabilites.py`, le repère **communautaire** de 1 % SC / 0 % SN / 99 % EC est appliqué **seulement** quand la caractéristique est attestée absente naturellement **et** que la rune utilisée a un poids connu strictement supérieur à 20. Le guide ne fournit **pas** de taux fixe pour les autres cas. Les taux de référence ne sont **jamais** importés comme observations.
- Dans `forgely_strategy.py`, l'avis indicatif tient aussi compte du poids de la rune par rapport au reliquat pour **signaler un risque**. Aucun score heuristique n'est présenté comme une probabilité mathématique réelle. Le moteur refuse toujours de conseiller un jet ou un puits non confirmés.
- Les recommandations du guide (répartir la remontée des lignes, utiliser le reliquat et distinguer over/exo/transcendance) restent des **stratégies communautaires**, à valider sur DOFUS 3, et non une formule officielle du serveur de jeu.
- Une rune de transcendance finalise l'objet et est décrite comme un cas distinct ; son fonctionnement n'est pas encore simulé ni automatisé.
- Le catalogue des 105 icônes et les observations personnelles restent locaux. **Aucun scénario simulé ne gonfle les statistiques réelles**.
- Limites : densités non vérifiées pour certaines runes, absence de base exhaustive des jets naturels par équipement, lecture OCR du puits/jet encore imparfaite ; validation Windows en partie réelle requise.

Tests : `py -3.13 -m unittest discover -s tests` depuis le dossier du projet.

## Version 0.17 — Moteur stratégique explicable (expérimental)

- **Nouveau module `forgely_decision.py`** : dictionnaire des poids *vérifiés*, distinction entre FM naturelle / over / exo quand les **jets naturels certifiés** sont connus, plafond communautaire de 101 poids ajouté, comptabilité prudente du reliquat, classement indicatif de runes candidates.
- L'interface principale ajoute **« Prochaine rune / stratégie »** ; le **clic droit sur le logo flottant** ouvre également le conseil, et le petit logo affiche la rune suggérée ou « Jet à lire ».
- Le conseil nécessite un **objectif sauvegardé**, une **fiche de l'objet reconnue ou sélectionnée**, trois lectures OCR stables du **jet et du reliquat**, et une relecture après toute fusion. Si la lecture reste incertaine, **aucune rune n'est suggérée**.
- **Attention :** la sélection des runes ne constitue PAS un calcul des vraies probabilités du moteur de DOFUS. C'est un **classement heuristique de candidats**, qui ne garantit pas le meilleur chemin vers le jet parfait. Les observations locales ne sont que des fréquences brutes et ne sont pas stratifiées par jet/puits.
- Le guide communautaire donne un repère 1% SC / 0% SN / 99% EC uniquement pour l'exo confirmé dont le **poids de rune est strictement supérieur à 20**. Les autres taux restent inconnus. Le moteur ne remplace pas un taux inconnu par un taux fictif.
- Exemple de confusion évitée : `Cri` = coups critiques (poids 10 dans le référentiel DOFUS 3), `Do Cri` = dommages critiques (poids 5). Ils n'ont pas le même effet.
- Le plafond communautaire de **101 poids d'over/exo** ne signifie PAS que les stats naturelles de l'objet sont limitées à 101. En l'absence de l'ensemble des jets naturels vérifiés, le logiciel indique « inconnu » pour la nature FM/over/exo.
- **Simulations hypothétiques / apprentissage par renforcement non entraîné :** le programme ne dispose pas d'une formule de transitions SC/SN/EC selon l'état pour reproduire le jeu. Des millions de simulations avec des chances supposées ne seraient pas des preuves et ne sont jamais ajoutés aux statistiques observées.
- Aucun clic, aucune manipulation de la fenêtre DOFUS, aucun envoi réseau pendant l'observation. Les données restent dans `%LOCALAPPDATA%\\Forgely`.
- **Validation nécessaire sur Windows avec DOFUS 3** : les régions OCR et les transitions restent sensibles au zoom et aux effets d'interface. Les tests Python valident les règles de sûreté, pas une exactitude de détection en jeu.

Pour lancer : `installer_windows.bat`, puis `demarrer_forgely.bat`, après avoir décompressé la version dans un dossier nouveau. L'ancienne version peut être conservée à part.

Sources d'orientation (guides communautaires, pas algorithme officiel) :
- https://huzounet.fr/guides/forgemagie
- https://www.dofuspourlesnoobs.com/guide-forgemagie.html
- https://www.tofus.fr/fiches/forgemagie

## Version 0.18 — Contextes de tentatives & recommandations prudentes

- La référence du dernier jet stable **avant** une fusion est désormais conservée au lieu d'être effacée immédiatement.
- Une fusion détectée suspend la recommandation affichée par le logo jusqu'à une nouvelle lecture stable **différente** du jet et du puits.
- Lorsque rune + résultat + équipement sont reconnus, et que deux relevés compatibles de jet/puits existent, un événement contextualisé est enregistré localement dans `fusion_contexts` (SQLite). Cela n'augmente pas le compteur des simulations.
- Le conseil examine les observations contextualisées d'une même rune sur le même équipement, avec un jet et un reliquat approximativement comparables. Sous 30 observations contextualisées, les pourcentages contextualisés restent masqués ; au-delà, il donne SC/SN/EC mesurés et un intervalle Wilson sur SC.
- Ces intervalles ne prouvent pas l'équivalence des situations ou la validité du moteur de jeu. Les recommandations restent heuristiques, pas le chemin optimal garanti.
- Les captures partielles ne certifient pas le jet complet de l'objet. Le titre, les lignes naturelles min/max et la rune effectivement tentée restent des limites majeures ; l'absence de l'une d'elles doit empêcher un conseil affirmatif.
- Aucun réseau pendant l'observation ; pas de clic ni de manipulation de DOFUS.
- `IDEES_FONCTIONNALITES.md` propose des ajouts classés par utilité et prérequis.

**Attention :** la capture OCR des zones et la lecture des jets n'ont pas été testées en conditions réelles sur Windows pour cette version. Les tests automatisés ne mesurent pas le taux de reconnaissance en jeu. Conservez l'ancienne archive pendant les essais.

## Version 0.19 — Stratégies, exports et galerie des réussites (locale)

Cette version conserve le fonctionnement **strictement local**. Sur l'accueil, utilisez
**« Réussites & outils »** ou la section **« Outils & réussites »** dans le menu latéral.
Le clic droit sur le logo flottant propose également **« Réussites, stratégies et sauvegarde »**.

### Fonctionnalités activées

- **Stratégies** : Prudent / Économique / Rapide / Jet parfait (préférences locales). La sélection de la stratégie n'est pas encore une optimisation par politique probabiliste entraînée ; le coach reste indicatif et attend les jets fiables.
- **Budget et prix des runes** : saisie de prix manuelle et calcul du coût partiel des essais observés pour l'item actuel. Si des prix manquent, l'estimation est signalée comme incomplète.
- **Simulation illustrative** : distribution SC/EC sur des probabilités saisies par l'utilisateur, sans copie du simulateur DOFUS et sans écriture dans les tentatives réelles.
- **Export CSV** : observations et tableau par équipement ; **sauvegarde ZIP** : base SQLite et préférences et jets naturels, s'ils sont présents.
- **Catalogue des jets naturels** : import d'un CSV préalablement vérifié, format `equipement,statistique,min,max`. Aucune récupération exhaustive automatique n'est garantie.
- **Galerie des réussites** : création de fiches locales avec nom de l'objet, objectifs et valeurs atteintes (pas de screenshot ni d'identifiant de personnage). Forgely refuse une fiche si une seule stat cible manque, si le jet n'est pas stable après fusion, si le reliquat est inconnu ou si l'objet n'est pas reconnu avec certitude. Le même jet/objectif ne génère pas un doublon. Les cartes peuvent être exportées manuellement en JSON.

### Ce qui reste expérimental ou à développer

1. **Reconnaissance parfaite de l'atelier** : calibrage selon résolution/échelle et validation contre des captures DOFUS réelles nécessaires.
2. **Catalogue exhaustif des équipements / jets naturels** : aucune base de jets officiels complète n'est incluse ; import CSV volontaire seulement.
3. **Prédiction de la probabilité d'atteindre le jet final** : aucun pourcentage n'est produit sans modèle de transitions validé ; le seuil atteint est constatable, pas la probabilité d'y parvenir.
4. **Conseil d'arrêt** : peut confirmer que tous les objectifs sont remplis si l'état est fiable ; ne peut pas garantir qu'arrêter est optimal dans les autres cas.
5. **Statistiques communautaires / galerie publique** : **non activées**. Aucun serveur, ni synchronisation, ni publication automatique n'existent dans cette version. L'export JSON est un aperçu local à partager éventuellement plus tard, uniquement avec la décision du joueur.
6. **Comparateur optimisé entre stratégies** : le simulateur est hypothétique et ne reproduit pas les transitions effectives de DOFUS. Ne pas utiliser ses résultats comme des probabilités réelles.

### Installation et données

Décompressez l'archive dans un dossier neuf. Sous Windows avec Python 3.13,
lancez `installer_windows.bat` puis `demarrer_forgely.bat`.
Les données demeurent sous `%LOCALAPPDATA%\\Forgely` dans une base locale SQLite,
avec une nouvelle table `success_gallery` créée à la première ouverture de la galerie.
La sauvegarde ZIP conserve aussi les cartes de réussites car elles sont dans cette base.
Ne pas supprimer votre ancien dossier de données sans sauvegarde.

### Validation

Les tests exécutables sont disponibles via : `python -m unittest discover -s tests`.
Ils testent les règles de création de cartes, l'anti-doublon, les exports et les composants métiers.
La compilation Python et les tests unitaires ne remplacent pas un essai graphique sur Windows/DOFUS 3.

## Version 0.19.1 — Correctif de reconnaissance de l'atelier

- Tolérance contrôlée aux erreurs OCR dans les **titres de métier** : par exemple `JOATLLOMAGE` peut maintenant être reconnu comme Joaillomagie. Le programme continuait auparavant à ignorer complètement les lectures lorsque le titre exact n'était pas reconnu.
- La sécurité reste active : aucun résultat ou nom de rune n'est inventé. L'historique doit changer de façon confirmée et la rune doit être identifiable pour entrer dans les statistiques.
- Attention : **la détection des runes ne fonctionne pas sans la position de l'icône sélectionnée calibrée**, sauf lorsque le nom est explicitement visible par OCR. Le catalogue de 105 icônes ne remplace pas la localisation de la case dans l'atelier.
- En cas d'échec, le bouton **Voir le diagnostic OCR** permet de lire le motif de rejet. La zone du titre est liée à la mise en page de la capture de référence ; changer l'échelle peut encore perturber la reconnaissance.
- Vérification faite par tests unitaires sous Linux ; non validée sur l'atelier réel Windows.

## 0.19.2 — Accueil allégé (correctif ergonomique)

L'écran principal ne montre plus les zones de diagnostic, l'import des icônes, les menus latéraux ou les panneaux multiples de probabilités. Il se concentre sur l'état de l'analyse, le conseil de prochaine rune, l'équipement, la dernière tentative et les fréquences SC/SN/EC observées. Les outils avancés sont accessibles sous « Plus », et le mode discret reste au premier plan.

Ce correctif **ne change pas le moteur OCR ni les taux** : les performances de reconnaissance en jeu restent expérimentales. Les informations incertaines ne doivent pas être interprétées comme une recommandation fiable. Le mode local est conservé.


Version 0.19.9 : voir README_RECHERCHE_FM.md (sources, contradictions, raisonnement).


**v0.20.1 :** voir `README_SOURCES_PROBAS_20_1.md` pour les nouvelles sources et les calculs de risque conditionnels.


## 0.20.4 — laboratoire vidéo
Voir `README_VIDEOS_20_4.md`. Index de trois vidéos, planches pour enregistrements locaux autorisés, feuille de revue et export strict des tentatives validées. Aucune tentative vidéo n’a encore été extraite.


## Préparation de mise en ligne (v0.20.15)

Voir [DEPLOIEMENT_CHECKLIST.md](DEPLOIEMENT_CHECKLIST.md) et [serveur/README.md](serveur/README.md). Prototype API non déployé ; aucune synchronisation client activée.


## Version 0.20.17 — Audit terrain
Voir `TEST_TERRAIN_20_17.md` pour exporter les tentatives en lecture seule et préparer leur vérification humaine.
