# Règles réellement utilisées par Forgely et son entraîneur

**État historique avant correction.** Les incohérences relevées ci-dessous ont été corrigées ensuite ; consulter [les règles harmonisées actuelles](REGLES_FM_HARMONISEES_2026-11-08.md). Ce texte est conservé pour expliquer l’origine des changements.

Audit local du 8 novembre 2026, après les ajouts vidéo et raisonnement. Ce document décrit **ce que fait le code**, pas une certification des règles du serveur Dofus. Aucun changement du moteur n’a été effectué pour cet audit.

## 1. Plusieurs niveaux, avec des rôles différents

1. **Comptabilité des observations** : vérifier les changements réellement lus et le reliquat.
2. **Conseiller** : comparer les runes disponibles et expliquer une proposition.
3. **Modèle prédictif issu des explications vidéo précédentes** : estimer SC/SN/EC sous des hypothèses déclarées. Ce nom ne désigne pas l’importateur de MP4.
4. **Simulateur local Dofocus** : produire des résultats virtuels et des pertes pour anticiper et entraîner.
5. **Entraîneur** : apprendre des choix dans ce simulateur, par objet et cible, puis comparer le jet complet obtenu à un témoin.
6. **Lecture des MP4** : transformer des passages lisibles en observations qualifiées et rapports. Elle n’imite pas automatiquement toutes les décisions du joueur filmé.

Le conseiller combine certaines de ces sources. Elles ne constituent pas une formule unique et ne doivent pas être confondues.

## 2. Poids et gains des runes

La table partagée contient 105 entrées, provenant d’une extraction client versionnée `poids_runes_client_3_7_13_17.json`. Elle n’est pas présentée comme une publication officielle d’Ankama. L’export CSV joint à cet audit contient **chaque rune, son gain et son poids exact utilisés**.

Principaux poids par point :

| Caractéristique | Poids |
|---|---:|
| PA | 100 |
| PM | 90 |
| Portée | 51 |
| Invocation | 30 |
| Dommages génériques | 20 |
| Dommages élémentaires | 5 |
| Résistance élémentaire en % | 6 |
| Sagesse | 3 |
| Prospection | 3 |
| Tacle / Fuite | 4 |
| Force / Intelligence / Chance / Agilité | 1 |
| Vitalité | 0,2 |
| Initiative | 0,1 |

Exemples : Vi +5 pèse 1 ; Pa Vi +15 pèse 3 ; Ra Vi +50 pèse 10. Les gains et tailles sont lus dans la table, pas déduits d’une règle universelle « simple +1, Pa +3, Ra +10 ».

## 3. Jets, objectifs, over et exo

- La **cible utilisateur est un minimum**. Le jet est atteint quand toutes les lignes ciblées valent au moins leur cible.
- Une ligne ciblée déjà atteinte ne reçoit plus de rune dans le conseiller ordinaire et l’entraînement classique.
- Une rune peut dépasser légèrement la cible si la valeur obtenue reste dans le maximum naturel connu.
- **Over** : valeur proposée supérieure au maximum naturel de cette caractéristique.
- **Exo** : caractéristique absente du profil naturel complet. Un profil incomplet ne suffit pas à affirmer son absence.
- Les objectifs explicites peuvent autoriser over/exo ; une simple lecture de ligne ne les autorise pas automatiquement.
- Une caractéristique absente de l’OCR reste inconnue : elle n’est pas mise à zéro.
- Pour un objet nommé, le conseiller exige son profil naturel complet et la lecture des lignes naturelles avant de conseiller. Après une fusion, il attend un nouveau jet stable.
- Les lignes négatives/malus ne sont pas considérées comme maîtrisées : le conseiller saute une cible négative ou à maximum naturel négatif ; les gardes retournent « non vérifiable ». Le raisonnement préparatoire refuse les profils contenant de telles valeurs. Le simulateur possède des branches signées, mais cela ne constitue pas une prise en charge complète et validée de la FM des malus.
- Objectif complet atteint : le conseiller propose d’arrêter ; l’entraîneur termine l’épisode, sans poursuivre pour créer un surplus.

## 4. Puits : comptabilité réelle contrôlée

Dans `pool_transition` et l’audit des observations :

- **SC** : gain nominal de la rune, aucune perte de caractéristique, puits conservé exactement. Un SC avec perte est contradictoire.
- **SN** : rune passée avec possibilité de pertes et/ou consommation de reliquat.
- **EC** : rune non passée, avec possibilité de pertes et/ou consommation de reliquat.
- Pour SN/EC : **puits après = max(0 ; puits avant + poids réellement perdu − poids de la rune tentée)**.
- Pour calculer les pertes sur la ligne visée en SN, le gain nominal est d’abord ajouté à la valeur avant : une différence nette seule sous-estimerait les pertes.
- Le puits n’est jamais négatif dans cette comptabilité et n’est pas remis à zéro par un SC.
- L’over existant n’est pas du puits disponible. Seule sa perte réellement constatée peut participer au reliquat, après déduction du poids tenté.

Exemples, en supposant que seules les pertes citées surviennent :

- Perte de 1 PA pendant une Pa Sa de poids 9 : gain net de puits 91, pas 100.
- Perte de 1 PO pendant une Pa Vi de poids 3 : gain net 48, pas 51.
- Perte de 3 Intelligence pendant une rune de poids 1 : gain net 2 ; pendant une rune de poids 3 : gain net 0.
- SC remettant un PA avec un puits de 17 : puits conservé à 17.

**Limite importante : le simulateur d’entraînement, décrit plus bas, plafonne encore le puits à 100 après une pose non SC. Cette limite n’existe pas dans la comptabilité d’observation et n’est pas une règle de jeu établie par cet audit.**

## 5. Gardes de légalité internes

Le conseiller utilise les gardes conservatrices suivantes :

- Pour une ligne en over, **poids total de la ligne résultante ≤ 101**, et non simplement poids des points en trop ≤ 101.
- Une ligne naturellement supérieure à 101 de poids reste autorisée tant qu’elle ne dépasse pas son maximum naturel.
- Densité des caractéristiques exotiques positives cumulées ≤ 101.
- Profil ou poids inconnus : état « non vérifiable », jamais preuve de légalité.
- Une limite documentée propre à l’objet, lorsqu’elle existe, est également appliquée.

Le simulateur Dofocus impose en plus sa propre limite de ligne `max(maximum naturel, floor(101 / poids unitaire))` et des contrôles de masse supplémentaire totale ≤ 101. Il existe donc une différence entre ses gardes et celles du conseiller. Ces seuils sont des **contraintes du logiciel actuel**, pas la preuve d’une loi universelle du jeu.

## 6. Comment le conseiller choisit une rune

### Candidats ordinaires

Pour chaque ligne ciblée encore insuffisante, il compare les tailles connues de cette famille. Il élimine les poses dépassant les gardes, les limites de l’objet ou les blocages du simulateur. Il calcule la valeur projetée avant de classer.

Lorsqu’il reste une ligne naturelle ciblée à remonter et qu’une pose naturelle est disponible, il **retire les poses finales over/exo des candidats ordinaires**. Ce choix privilégie le remontage avant la finition exotique. Ce n’est pas une règle disant de toujours remettre immédiatement un PA/PM/PO naturel absent.

### Score de base exact

Notations : `g` = gain rune ; `w` = poids rune ; `c` = valeur actuelle ; `t` = cible ; `p` = puits ; `M` = maximum naturel.

- Progression : `min(1 ; g / (t-c))`.
- Exposition : `max(0 ; w-p) / max(w ; 1)` : indicateur de risque, pas perte attendue réelle.
- Équilibrage de ligne : `0,15 × max(0 ; 1-c/M)` si M > 0.
- Dépassement : `max(0 ; c+g-t) / max(1 ; t-c)` ; si le modèle prédictif seul classe, le dénominateur devient `max(1 ; g)`.
- Pression de taille : `min(4 ; max(0 ; c/(20g)-1))`, sauf quand le modèle prédictif seul classe, où elle vaut zéro. Ce n’est pas une interdiction de passer une petite rune au-dessus de 20 fois son gain.
- Pénalité de finition : 0,8 pour over/exo si du naturel ciblé reste à remonter, sinon zéro.
- Utilité initiale : `(progression + équilibrage) / (1 + 0,7×exposition×facteur_non_SC + 0,5×pression + dépassement)`.
- Division par `1 + pénalité_finition`, correction par les sources comparables, puis score `utilité − 0,04×w/100 − pénalité_finition`.
- Quand seul le modèle prédictif est disponible, le facteur non-SC vaut `(100-SC)/100` et l’utilité est multipliée par `(SC+SN)/100`.

L’ordre lourd → léger n’est **pas imposé universellement**. Le choix dépend de la progression, de l’exposition, des données comparables et, lorsqu’elles sont disponibles, des suites virtuelles.

### Anticipation et données réelles

- Le travailleur local peut effectuer 48 essais à une pose par rune par défaut, puis des anticipations de 8 poses : 16 essais pour une première recherche, 32 pour affiner et vérifier.
- Dans ces suites, atteindre le **jet complet** domine les progrès partiels. Une décision future est recalculée après chaque résultat simulé.
- La première pose peut être calibrée par des observations comparables ; cela ne calibre pas automatiquement la distribution réelle de toutes les pertes ni les poses futures.
- La validation courte exige une absence de régression observée par rapport au témoin ; elle est explicitement différente d’une preuve de supériorité statistique en jeu.
- Si toutes les runes candidates possèdent une anticipation, la valeur de ces suites peut remplacer le score immédiat.
- Les comptages agrégés tous jets confondus restent descriptifs. Les corrections exigent le même objet et la même rune ; les comptages exacts distinguent jet et puits.
- Les corrections contextuelles utilisent au moins 30 observations. Le mélange configuré est 40 % modèle / 60 % données comparables, **avec repli sur la seule source disponible**. Ce n’est pas partout un mélange brut et fixe de pourcentages.
- Pour les suites, les comptages OCR non vérifiés ont une confiance réduite à 0,25 ; la fiabilité vaut `confiance × n/(n+100)` avant mélange.
- L’expérience de jets voisins peut modifier un score dans une plage bornée 0,85–1,10, sans être transformée en nombre de tentatives exactes ni en probabilité serveur. Les voisins doivent respecter des contraintes strictes de proximité de jet, même régime d’over, puits et lignes lourdes identiques.
- Une politique entraînée compatible et auditée n’apporte qu’un facteur borné 0,8–1,2 à la part simulée.

### Prix et budget

- En mode Chances maximales, le prix peut départager des choix équivalents lorsqu’il est connu pour tous.
- En mode Budget optimisé, si les prix de tous les candidats sont connus, un score positif est divisé par `1+prix unitaire`. Prix inconnu ≠ rune gratuite.
- Le budget continue par défaut à produire une alerte en maintenant les conseils. La suspension n’a lieu que si l’option correspondante est activée.
- L’objectif de l’entraîneur virtuel n’intègre pas de monnaie.

## 7. Modèle prédictif séparé : hypothèses numériques

`forgely_predictive.estimate` utilise une moyenne **non pondérée** Q des ratios de remplissage de toutes les lignes naturelles positives, chacun borné entre 0 et 1. Un exo PA, PM ou PO présent impose Q = 1.

Pour une ligne naturelle positive, difficulté D :

- Base : 5.
- Seuil : +45 si la valeur actuelle atteint 80 % du maximum naturel.
- Over projeté : +65, puis +4 par poids de surplus projeté.
- Taille : `+12×max(0 ; valeur_actuelle/gain_rune − 14)`.
- Qualité : `+60×Q^12`.
- Si niveau < 170 : `−20×max(0 ; 1,1−Q)` ; si niveau inconnu, ce bonus n’est pas appliqué.

`x=(100−D)/2`, puis SC borné entre 2 et 100 %. SN est reconstruit par morceaux : `min(50 ; 100−SC)` si x≥0, sinon `max(15 ; 50−0,75×abs(x))`, avec −10 en over, puis bornage entre 0 et `100−SC`. EC complète à 100 %.

Pour une caractéristique absente d’un profil complet et une rune de poids > 20 : référence communautaire SC 1 %, SN 0 %, EC 99 %. Elle n’est pas une mesure officielle et ne couvre pas tous les exos légers.

Calibration des observations certifiées : à partir de 30 essais exactement comparables, moyenne pondérée par un a priori de 200 essais : `(200×prédiction + 100×comptage_résultat)/(200+n)`. Les observations vidéo qualifiées peuvent entrer dans cette calibration. Ce mécanisme est distinct du mélange 40/60 des scores et anticipations.

## 8. Simulateur utilisé par l’entraîneur

Version : `dofocus-2026-11-07-6a559153678e`. Implémentation indépendante d’un comportement observé du simulateur public Dofocus, **pas de l’algorithme serveur confirmé**.

### Probabilités

Pour une ligne naturelle, Q est ici un **remplissage pondéré par les poids**, hors ligne visée et hors lignes négatives. C’est différent du Q précédent. Un exo PA/PM présent impose Q = 1.

Difficulté : `5 + 4×poids_rune×max(0 ; valeur/gain−14) + 60×Q^12`. En over : ajout `65+4×poids_surplus`. Sinon, sur une ligne non fixe, ajout de 45 si la **valeur projetée** atteint 80 % de l’intervalle min–max. Bonus sous niveau 170 : `−20×max(0 ;1,1−Q)` ; sous niveau 100 : encore −15.

SC : `max(2 ; (100−D)/2)`. SN naturel : `min(50 ;100−SC)` si D≤100, sinon `50−0,375×(D−100)`. En over, SN : `max(5 ;40−0,375×(D−100))`. SN est ensuite borné entre 0 et `100−SC` ; EC complète à 100 %.

**Exos PA/PM/PO absents : SC 1,5 %, SN 0 %, EC 98,5 % dans ce simulateur.** Ce n’est pas la référence 1 % du modèle prédictif séparé. Pour les autres exos, une courbe spécifique dépend de la densité projetée, de Q et du niveau ; le code comporte aussi un régime spécial distinct. La courbe complète est dans `odds()` ; aucun taux unique pour tous les exos n’est utilisé.

Courbe exacte des autres exos ordinaires : pour densité projetée d, base B = 57 si d≤2 ; `57−(d−2)×38/13` si 2<d≤15 ; `19−(d−15)×1,9` si 15<d<25 ; sinon 0. Sous niveau 100 et d≤50, B est au moins `8−5×(d−25)/25`. Si B≤0 : SC 1, SN 0, EC 99. Sinon A = `max(1 ;0,077B)+0,923B`, L = `A/(100−A)×exp(1,2×(0,85−Q))`, réussite S = `max(1 ;100L/(1+L))`, SC = `max(1 ;0,077S)`, SN = S−SC, EC = 100−S. Les valeurs sont des pourcentages. Le régime interne `@special` possède SC 1 / SN 34 / EC 65 ; il ne constitue pas une règle des runes ordinaires de l’interface.

### Résultats et pertes

- Tirage aléatoire selon les probabilités simulées.
- SC : ajout nominal, aucune perte, puits conservé.
- SN : ajout nominal puis paiement du poids simulé.
- EC : pas d’ajout, paiement du poids simulé.
- Les lignes en surplus/exo autres que la ligne visée sont examinées d’abord, dans un ordre aléatoire, avec une probabilité d’absorption dépendant de la charge et du poids unitaire.
- Ensuite, le puits absorbe le reste ; puis peuvent être sollicités le surplus de la ligne visée et les lignes naturelles. Le choix et les quantités perdues sont aléatoires, avec des pondérations internes.
- La sélection des lignes naturelles utilise notamment `min(1 ; charge/poids_unitaire)` et un facteur 1/60 pour la ligne visée. Certaines petites densités peuvent perdre un point supplémentaire avec une probabilité interne de 29 %.
- Une perte plus lourde que la charge restante peut créer du puits.
- Les branches signées peuvent utiliser un demi-poids quand la valeur projetée reste négative. Elles ne remplacent pas une validation complète des malus.
- Après les pertes non SC, **puits simulé borné à [0 ;100] et arrondi au centième**. L’observation réelle, elle, n’a pas ce plafond.

Il n’existe aucune garantie que l’over saute intégralement, qu’une grosse ligne choisie tombe, ou que le puits protège toujours toutes les autres lignes. Les priorités de perte et coefficients ci-dessus sont des **approximations du simulateur**.

## 9. Ce que l’entraîneur apprend

- Une politique est liée à l’objet, son profil naturel, les cibles, le modèle et les réglages compatibles. Pas de mélange automatique entre deux objets.
- Départ sélectionnable minimum / moyen / maximum ; moyen = milieu arrondi de chaque borne naturelle. Une ligne exo ciblée démarre à zéro.
- Dans l’interface : 1 000 épisodes, 200 poses maximum, 200 épisodes de vérification et puits initial 0 par défaut. L’API TrainingConfig possède un défaut distinct de 100 poses ; l’interface lui passe explicitement 200.
- Sans stock fourni, le stock simulé est illimité. Un stock explicite est décrémenté à chaque rune.
- Arrêt si toutes les cibles sont atteintes, limite de poses, arrêt utilisateur ou absence d’action exploitable.
- Récompense : déficit `Δ = somme(max(0 ; cible−valeur) × poids_unitaire)` ; potentiel `0,1/(1+Δ)`. Récompense = variation du potentiel, plus 1 si le jet complet vient d’être atteint. En échec final/abandon, potentiel final annulé.
- Aucun bonus pour gagner du puits, créer un over, réussir une seule belle ligne ou économiser des kamas. Atteindre tout le jet prime.
- Apprentissage tabulaire par essais : exploration `max(0,05 ;0,30/(1+épisodes_déjà_vus/1000))`, mise à jour avec pas `max(0,05 ; visites_action^−0,6)`, valeur future non actualisée. Jusqu’à 50 000 états ; un réservoir de 64 états difficiles permet du rejeu un épisode sur quatre.
- Le témoin direct favorise `(SC+SN) × progression_relative / (1+exposition)`. Il ne récompense pas une préparation sans progression immédiate.
- L’état classique discrétise certaines valeurs en 16 niveaux relatifs, le puits par tranches de 2, et l’horizon en 16 niveaux. Ce n’est pas une mémorisation exacte de tous les jets possibles.
- Les graines d’entraînement, de vérification et d’audit sont séparées. Les archives restent conservées ; la dernière sauvegarde ne remplace pas automatiquement un meilleur modèle.
- Activation ordinaire : il faut une vérification du jet complet d’au moins 50 épisodes par bras, avec borne basse de Wilson à 95 % de la politique supérieure à la borne haute du témoin. Les politiques généralisables demandent en plus leur audit de sélection compatible. Un succès apparent dans quelques épisodes ne suffit pas.

### Recherche généralisable optionnelle

Huit configurations de quatre coefficients sont comparées dans des trajectoires simulées. Le score associe réussite simulée, progression pondérée en poids, déficit restant, exposition au puits et dépassement. Cette recherche est une politique compacte, pas un apprentissage de toutes les règles réelles du serveur. Elle est désactivée par défaut.

### Préparation / over temporaire optionnels

- Mode expérimental désactivé par défaut ; incompatible actuellement avec la recherche généralisable simultanée.
- Peut ajouter une petite rune sur une ligne naturelle positive existante de Vitalité, Force, Intelligence, Chance ou Agilité, alors qu’elle n’a plus de déficit ciblé, pour étudier une ligne support ou un surplus.
- Utilise la plus petite rune connue de la famille ; surplus résultant limité à **3 PWR au-dessus du maximum naturel**, sous les autres gardes.
- Ne crée pas de caractéristique absente et ne poursuit pas un jet déjà entièrement atteint.
- Les états distinguent alors exactement les valeurs au maximum ou en surplus. Aucun puits fictif ni récompense supplémentaire.
- Les politiques issues de ce mode sont **exclues des conseils actifs** tant qu’un audit adapté de la sélection en direct n’est pas disponible. Le conseiller les présente comme options à comparer, pas comme une rune optimale démontrée.
- Les essais réalisés sur plusieurs objets n’ont pas démontré de gain global. La stratégie reste étudiable ; son efficacité en jeu n’est pas déduite du résultat de ce simulateur.

## 10. Règles d’apprentissage des vidéos réelles

- Images seulement, aucun audio, aucune action dans le jeu.
- Reconnaissance séparée : objet, jet, rune, journal et puits. Plusieurs lectures stables et un nouvel événement distinct sont nécessaires.
- Le décalage du journal doit prouver une nouvelle ligne de résultat ; une ligne persistante n’est pas une nouvelle tentative.
- Une stabilisation après l’événement est attendue ; les changements du jet et du journal peuvent arriver dans les deux ordres.
- Plusieurs tentatives avant une association fiable rendent les associations ambiguës ; une coupe, un changement d’objet ou une lecture insuffisante coupe l’appariement.
- Jet complet, profil naturel reconnu, puits connu et comptabilité cohérente nécessaires à la qualification. Les malus ou contextes non vérifiables ne sont pas promus silencieusement.
- Une correction peut résoudre une rune illisible ; elle ne transforme pas une séquence de plusieurs essais en essai unique.
- Même contenu MP4 : identifiant stable. Retransmission : remplace les contributions précédentes, y compris après rejet. Deux montages différents de la même session ne sont pas automatiquement dédoublonnés.
- Stockage vidéo séparé ; calibration prédictive possible sur données exactes qualifiées. Le simulateur virtuel d’entraînement ne change pas automatiquement toutes ses probabilités ou priorités de perte à chaque vidéo importée.
- Observer une bonne décision ou un jet réussi ne prouve pas la supériorité de la stratégie. L’objectif du joueur filmé peut être inconnu.

## 11. Règles qui ne sont pas imposées actuellement

- Pas de « SC remet le puits à zéro ».
- Pas de « PA qui saute donne toujours 100 de puits net ».
- Pas de « fabriquer un over crée immédiatement du puits ».
- Pas de « toujours casser le PA/PM/PO », « toujours le remettre immédiatement » ou « toujours le remettre à la fin ».
- Pas de seuil universel imposant de repasser exactement à 51/90/100 de puits.
- Pas de règle universelle lourd → léger, ni de taux officiel garanti pour toutes les runes.
- Pas d’apprentissage automatique de la stratégie entière de DofusFM : seuls les principes vérifiables ont été réimplémentés et testés. Son ordre exact de priorités et sa formule complète restent inconnus.
- Pas d’activation des overs temporaires en conseil principal à partir des seuls essais actuels.
- Pas de garantie de réussite ou d’égalité de performance avec un bot tiers.

## 12. Points à harmoniser identifiés par cet audit

1. Plafond de puits 100 dans les transitions simulées, absent de la comptabilité réelle.
2. Deux modèles numériques différents : Q, seuil de 80 %, pression de taille, SN et références d’exos divergent.
3. Gardes over/exo du conseiller et du simulateur pas entièrement identiques.
4. Malus non maîtrisés de bout en bout.
5. Les vidéos calibrent certaines estimations ; elles ne réentraînent pas encore automatiquement toute la physique du simulateur.
6. Les préparations restent une exploration expérimentale, pas une stratégie complète de balancier, casse ciblée ou gestion de grosse ligne déjà validée.

Ces constats expliquent pourquoi « intégré » ne signifie pas « identique au bot » ou « même taux réel ». Les corriger demande des choix de modèle et des essais ; cet audit ne les masque pas derrière une promesse.

## Sources locales

`forgely_weights.py`, `forgely_dofocus.py`, `forgely_rules.py`, `forgely_decision.py`, `forgely_predictive.py`, `forgely_dofocus_engine.py`, `forgely_sequence.py`, `forgely_simulation_live.py`, `forgely_online_experience.py`, `forgely_pricing.py`, `forgely_rl.py`, `forgely_training.py`, `forgely_general_policy.py`, `forgely_trained_policy.py`, `forgely_reasoning.py`, `forgely_expert.py`, modules vidéo et raccordement actif dans `forgely.py`.

Les empreintes des sources et les 105 entrées de poids sont enregistrées dans les fichiers d’audit joints.

- [Poids et gains des 105 runes](POIDS_RUNES_UTILISES_2026-11-08.csv)
- [Versions et empreintes des sources auditées](AUDIT_REGLES_FM_2026-11-08.json)
