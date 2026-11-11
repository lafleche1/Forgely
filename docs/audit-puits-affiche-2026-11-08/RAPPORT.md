# Forgely et stratégie « Puits Affiché » — audit du 8 novembre 2026

Le dépôt privé **lafleche1/Forgely** est accessible via le connecteur GitHub.
La branche `main` examinée pointe sur `f3d94809126a6d452c028e8ac72d63b312dca3e4`
(8 novembre 2026, 14 h 47 à Paris). Son VERSION.txt annonce 22.05.
La copie PC annonce **22.16**, avec des fonctions supplémentaires et un rapport
de fusion désignant précisément ce commit comme base distante. Remplacer les
sources PC par main ferait perdre des fonctions locales.

**Résultat : conserver le moteur prudent sur le puits insuffisant ; revoir la
matrice qui filtre les actions et harmoniser les modèles avant de comparer des
stratégies d’entraînement. La stratégie fournie n’est pas infaillible.**

Aucun fichier de production n’a été modifié. Les propositions ci-dessous sont
appuyées par des reproductions exécutées ; leurs implémentations et leur gain en
jeu ne sont pas validés. Les tests de l’existant ne prouvent pas une correction.

## 1. Accès et limites

- Le nom du compte est `lafleche1`, sans espace. La recherche des dépôts installés
  trouve Forgely ; la liste accessible pour ce propriétaire contient ce seul dépôt.
- Aucun dépôt distinct Forgely-Entraînement n’a été trouvé dans les accès de cette
  connexion. Cela ne prouve pas son inexistence ailleurs.
- L’arbre complet de main, non tronqué, ne contient aucun chemin correspondant à
  `entrain` ou `training`. Les lectures distantes de `forgely_training.py`,
  `forgely_dofocus_engine.py`, `forgely_reasoning.py` et `forgely_pool_ledger.py`
  à leurs chemins locaux donnent 404. Leur contenu local n’est pas attribué à main.
- Les sources d’entraînement sont disponibles sur le PC : entrée Python, moteur,
  environnement d’apprentissage et lanceur Windows. Le lanceur C# lance
  `.venv/Scripts/pythonw.exe Application/entrainer_forgely.py`.
  L’exécutable présent n’a pas été décompilé, exécuté ou recompilé pour cet audit ;
  son identité avec les sources actuelles n’est donc pas certifiée.
- Le dossier PC n’a pas de métadonnées Git utilisables : impossible d’établir sa
  filiation par `git status` ou `git log`. La version, le contenu et les empreintes
  permettent une comparaison, pas une preuve de filiation de tous les fichiers.
- La conversation référencée a été lue. Le texte utilisateur conservé est tronqué
  après le début de la section 2. Aucun script complet « infaillible » ou règle
  additionnelle sur les Ra Vi n’a été inventé pour compléter cette lacune.

## 2. Algorithmes réellement présents

**GitHub main.** `forgely_strategy.recommend` appelle `forgely_decision.advise`.
Les candidats sont des runes sur des lignes ciblées encore déficitaires. Le score
combine progression vers la cible, équilibre, dépassement, exposition
`max(0, poids_rune - puits)`, et probabilités du modèle vidéo quand disponibles.
Les lignes naturelles ciblées à réparer passent avant un over/exo final.
Les prix et budgets peuvent encore filtrer les candidats de cette version.
Les modèles et fréquences observées sont distingués des probabilités officielles.

**PC 22.16.** Le moteur ajoute preuves contextuelles, expérience, simulation locale
Dofocus et anticipations de séquences. Cependant `forgely.py` et
`MeasuredGoals.proposal` passent `predictive_policy=True` : le résultat de ce
classement est ensuite filtré et reclassé par `rank_options`.
Cette matrice emploie les phases **>=51, 20–<51, 0–<20, zéro**, et non les trois
cas de la stratégie fournie. Elle peut annuler un choix soutenu par le moteur.
Les bandes 60–70 %, 30–45 %, etc. de cette matrice sont des hypothèses utilisateur
étiquetées comme telles, pas une calibration ni la chance du jet final.

**Entraînement PC.** `ForgemagingEnv` emploie `odds/attempt` du modèle local
Dofocus. Les actions visent les déficits ciblés ; la préparation par surplus
léger est une option explicite. `_heuristic` classe approximativement par
`(SC+SN) × progression / (1 + exposition_relative)`, sans le filtre de phases
du copilote. La récompense privilégie le jet complet. Les politiques apprises
doivent franchir des contrôles de compatibilité et d’évaluation avant d’influencer
les conseils ; leur entraînement ne constitue pas une observation réelle.

## 3. Comparaison des mécanismes et règles

| Hypothèse fournie | Constat précis | Conséquence recommandée |
|---|---|---|
| Puits positif = protection totale | Faux comme garantie dans les modèles examinés : dépend du poids, des pertes et des surplus/ajouts fragiles. | Exposer le poids non couvert et les lignes fragiles. Ne pas promettre la conservation du jet. |
| Ignorer Pods, prospection, malus | Le moteur ne cible pas une ligne sans objectif. Une ligne ainsi délaissée peut néanmoins subir des pertes. Les malus sont exclus du classement positif courant. | Respecter les cibles choisies ; ne jamais déduire qu’une ligne est inutile de son nom. Améliorer un malus peut être un objectif réel. |
| Priorité densités 6 à 30 dès que puits >0 | La matrice PC ne le fait que partiellement : très gros puits sélectionne certaines lignes lourdes, moyen préfère Sagesse/Soins/Do critiques, faible ne garde que les caractéristiques légères. | Préférer une priorité souple dépendant de la cible et du poids disponible ; mesurer l’ordre sur le jet complet. |
| Max naturel +1 systématique | Non effectué par le conseil normal. Un over peut devenir une perte prioritaire lors d’une pose ultérieure. Les surplus préparatoires restent expérimentaux, sans puits futur crédité. | Ne préparer un surplus que dans une comparaison explicite ; arrêter au jet cible atteint. |
| « Coup franc » : puits 2, rune 10/20, déficit gratuit | Non confirmé par une source officielle et contredit par les moteurs locaux : le déficit peut coûter des caractéristiques. | Rejeter l’obligation de grosse rune. SC conserve le puits ; SN/EC peuvent consommer le puits et dégrader l’objet. |
| Puits zéro : tout SN détruit une autre ligne | Trop absolu : les modèles peuvent retirer le gain sur la ligne ciblée ; une perte n’est pas forcément sur une autre ligne. Les observations nettes ne suffisent pas toujours à identifier le mécanisme. | Montrer les transitions complètes ; ne pas assimiler un SN à un gain net garanti. |
| Bombarder pour faire sauter PA/PM/PO | Une chute est possible mais non garantie. Le moteur ne crédite pas sa valeur avant constat. | Comparer progression, réparation et risque sur un horizon borné ; aucun cycle infini garanti. |
| Rhabillage à la fin | Un PA naturel manquant reste une réparation naturelle, pas un exo. Le conseil peut le réparer avant un over final ; la matrice peut aussi le bloquer avec un faible puits. | Comparer les ordres. Remettre le PA/PM peut détruire un over ; le résultat souhaité exige parfois un SC. |
| Exo = 1 % | Le modèle vidéo donne 1 % à certains exos lourds ; le modèle Dofocus donne 1,5 % pour PA/PM/PO absents. Les autres exos n’ont pas tous ce taux. | Afficher la provenance ; ne pas présenter un taux universel ni remplacer une reproduction Dofocus par une prétendue vérité serveur. |
| Plafond over = maximum naturel +101 de poids | Ce n’est pas la garde utilisée : une ligne over doit avoir une densité totale <=101 ; une ligne naturellement plus lourde reste autorisée dans son maximum naturel. | Distinguer densité totale, surplus, exo et profil inconnu. Les gardes ne prouvent pas le passage d’une rune. |

**Poids effectivement chargés et contrôlés :** Ra Ine +10 / poids 10 ; Do +1 /
20 ; Do Feu +1 / 5 ; Cri +1 / 10 ; Ga Pa 100 ; Ga Pme 90 ; Po 51 ;
Ra Vi +50 / 10. « Dommages » génériques et élémentaires ne sont pas interchangeables.
Les % résistances élémentaires ont un poids unitaire de 6 dans le référentiel.
La table utilisée vient d’une extraction tierce des données du client, versionnée
et assortie d’empreintes, pas d’une publication certifiée Ankama.

La comptabilité `P' = max(0, P + poids_perdu - poids_rune)` sur SN/EC décrit le
reliquat après une transition connue. **Le max à zéro ne prouve pas que les pertes
manquantes sont gratuites.** Pour SC, le puits est conservé dans les modèles.
`PoolLedger` exige une base et une transition complète ; une observation manquante
ne permet pas de reconstruire magiquement le puits. Les malus demandent une
validation spécifique : le simulateur Dofocus applique parfois un demi-poids,
alors que le ledger observé additionne les pertes signées au poids unitaire.
Ce dernier point n’a pas été validé dans le jeu.

## 4. Écarts reproduits et corrections proposées

**Priorité haute — éviter les blocages par phase.** Force 20, cible 40, maximum
40, puits 51 : le classement ordinaire trouve une rune ; la matrice ne propose
rien car aucune ligne lourde n’est à réparer. Dommages 0, cible/max 1, puits 2 :
même blocage, car la phase faible exclut cette ligne. L’entraîneur continue à agir
sur le premier état. `test_large_pool_never_invents_a_heavy_target` entérine même
le premier blocage : c’est une politique actuelle, pas une simple faute de frappe.

Correction proposée : faire des phases une préférence souple. Si leur filtre
vide une liste de candidats déjà légaux, conserver la liste initiale et expliquer
l’exposition. Ne jamais inventer une cible lourde. Tests d’acceptation à ajouter :
les deux états ci-dessus gardent un conseil légal ; aucune proposition sur une
ligne hors cible ; aucune rune illégale réintroduite. Modification non appliquée,
car elle change une politique utilisateur explicitement codée et testée.

**Priorité haute — comparer le même décideur.** Le filtre de phases peut remplacer
le résultat des séquences et l’entraîneur ne l’utilise pas. Évaluer une politique
dans l’entraîneur seul ne suffit donc pas à prouver son intérêt dans le copilote.
Correction proposée : un sélecteur explicite partagé et versionné, puis des
épisodes comparatifs sur les mêmes états et graines. Conserver les contrôles de
promotion actuels : aucun gain en jeu n’est établi par cet audit.

**Priorité haute — rendre les modèles divergents visibles.** Les taux d’exo PA
1 et 1,5 % sont reproduits. Il faut sélectionner/nommer le modèle dans le résultat,
dans l’évaluation et dans le rapport, et ne pas faire passer une hypothèse pour
une mesure. Le champ interne `estimated=False` de Dofocus ne certifie pas Ankama.

**Priorité moyenne — plafonnement du puits.** Avec 150 de puits et un SN de rune
poids 1, le ledger arithmétique conserve 149, mais le simulateur local ramène à
100. Ce plafonnement est écrit dans `_losses`. Correction proposée : signaler cet
écart de modèle et empêcher une évaluation de politique hors domaine vérifié de
devenir une preuve de gain réel. Ne pas supprimer le plafond de la reproduction
Dofocus sans changer son identifiant et ses tests de parité. Le maximum réel du
reliquat côté serveur n’a pas été établi ici.

**Priorité moyenne — rhabillage et malus.** Ajouter des scénarios dédiés : PA/PM
naturel absent contre véritable exo, risque de destruction du surplus, franchissement
de zéro et prix en poids du malus. Garder « inconnu » quand la preuve manque.
Une borne/une formule du modèle n’est pas une règle serveur vérifiée.

**Stratégie corrigée proposée :** confirmer jet, profil, cibles et puits ; arrêter
si toutes les cibles sont atteintes ; énumérer les runes légales vers les déficits ;
comparer gain, pertes exposées et réparation du jet complet ; utiliser la phase
comme préférence ; exécuter une seule décision et relire. Comparer toute
préparation max+1 et tout ordre de rhabillage dans des scénarios explicitement
simulés. Aucun coup franc gratuit ou nombre de cycles garanti.

## 5. Validation exécutée pendant cet audit

- `audit_checks.py` : **17 contrôles réussis**. Inclut poids, SC/SN/EC avec puits
  insuffisant, arrêt faute de distribution de pertes, chute PA moins poids de rune,
  plafond de ligne, réparation naturelle, arrêt sur cible et divergences ci-dessus.
- Exemple déterministe, probabilités forcées pour tester les transitions et non
  estimer leur fréquence : Intelligence 20, Force 40, puits 2, Ra Ine.
  SC donne Intelligence 30, Force 40, puits 2 ; SN donne Intelligence 30,
  Force 32, puits 0 ; EC donne Intelligence 20, Force 32, puits 0.
  Ces résultats démontrent le comportement du modèle, pas une expérience DOFUS.
- Suite ciblée : **830 tests réussis en 7,64 s**. Fichiers :
  `Tests/test_dofocus_local_engine.py`, `test_pool_ledger.py`, `test_pool_observer.py`,
  `test_predictive_matrix.py`, `test_reasoning_candidates.py`, `test_rl_environment.py`,
  `test_training_regressions.py`, `test_training_runner.py`, `test_sequence_planning.py`,
  `Application/tests/test_fm_objectives.py`, `test_predictive_video.py`.
- Le premier lancement avait 804 réussites et 26 erreurs de préparation liées
  au dossier temporaire Windows inaccessible. Le même ensemble a été relancé
  avec un dossier temporaire neuf dans le projet : 830 réussites, zéro erreur.
  Les deux comptes rendus XML sont conservés.
- Aucune suite graphique, campagne longue, reconstruction d’exécutable, essai
  dans DOFUS ou certification des probabilités serveur n’est revendiqué.

## 6. Fichiers réellement examinés et changements

Huit fichiers distants complets sont conservés dans `github-sources.json`, lus au
commit fixé : `VERSION.txt` et, sous `Application/`, `forgely_strategy.py`,
`forgely_decision.py`, `forgely_virtual.py`, `forgely_predictive.py`,
`forgely_rules.py`, `forgely_weights.py`, `forgely_dofocus.py`.
Les empreintes Git des contenus téléchargés sont vérifiées par le script d’audit.
Seuls strategy et weights ont le même texte que le PC parmi ces huit chemins.
Les autres différences de contenu ne sont pas effacées.

Sources locales lues intégralement ou par sections pertinentes : ces mêmes huit
chemins, puis `Application/forgely_fm_model.py`, `forgely_reasoning.py`,
`forgely_dofocus_engine.py`, `forgely_pool_ledger.py`, `forgely_pool_observer.py`,
`forgely_simulateur.py`, `forgely_rl.py`, `forgely_training.py`,
`forgely_simulation_live.py`, `forgely_measured_goals.py`, `forgely.py`,
`entrainer_forgely.py`, `lanceur_entrainement.cs`. Les lectures de `forgely.py`
et des grands modules d’entraînement sont ciblées, pas une revue exhaustive.
Documentation lue : README, VERSION, `docs/POIDS_RUNES.md`,
`docs/FUSION_PC_GITHUB_2026-11-08.md`, `docs/dofocus-algorithm-findings.md` ;
en-têtes de `reference_sources_fm.csv` et `reference_poids_fm.csv`, pytest.ini.
Tests lus directement : `test_reliquat.py`, `test_v2080_pool.py`,
`test_pool_ledger.py`, `test_reasoning_candidates.py`, `test_predictive_matrix.py`,
`test_dofocus_local_engine.py`, sections de `test_training_regressions.py` et
`test_advice_source_weights.py`. L’exécution d’un test ne constitue pas à elle seule
une revue manuelle de tout son fichier.

**Ajouts uniquement dans ce dossier d’audit :** ce rapport, `audit_checks.py`,
`github-sources.json`, `results.json`, `pytest-results.xml` (premier lancement),
`pytest-results-workspace.xml` (relancement réussi).
Pytest a également produit ses données temporaires dans
`.test-tmp/audit-puits-01a1bc1c-20261108` et peut actualiser ses caches habituels.
**Aucun fichier de l’application remplacé, aucune synchronisation, aucun commit,
aucune écriture GitHub, aucun changement des historiques d’entraînement.**
Les 215 sources Python de l’arbre Application ont des empreintes conservées
dans `results.json` ; elles sont contrôlées avant/après les vérifications.

## 7. Sources externes et niveau de preuve

- [Dépôt privé au commit examiné](https://github.com/lafleche1/Forgely/tree/f3d94809126a6d452c028e8ac72d63b312dca3e4) : preuve du code distant, pas des règles du jeu.
- [Release dofus-sqlite 6.0_3.7.13.17](https://github.com/ledouxm/dofus-sqlite/releases/tag/v6.0_3.7.13.17) : origine tierce du référentiel numérique documenté localement ; les assets de cette release n’ont pas été retéléchargés pour cet audit.
- [Simulateur Dofocus](https://dofocus.fr/forgemagie/) : page consultée ; l’extraction Web expose surtout la navigation et une vérification d’accès aux prix. Pas de nouvelle reconstitution du JavaScript du site ici. La parité testée repose sur les fixtures locales et l’analyse antérieure identifiée par empreinte dans `dofocus-algorithm-findings.md`.
- Les recherches de documentation officielle Ankama sur ces cas n’ont pas fourni de spécification exploitable. Aucun plafond, taux universel, ordre de pertes ou « coup franc » n’est présenté comme officiellement certifié. Les guides historiques et serveurs privés trouvés ne sont pas utilisés pour certifier DOFUS actuel.

Reproduction : depuis la racine du projet, lancer
`.venv/Scripts/python.exe docs/audit-puits-affiche-2026-11-08/audit_checks.py`.
Les contrôles constatant des divergences sont des sondes d’audit de l’état actuel,
pas des contrats de comportement à conserver après une future correction.
