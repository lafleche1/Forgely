> Mise à jour : le modèle vidéo est désormais prioritaire et les transitions réelles qualifiées calibrent les estimations. Les descriptions anciennes de taux indisponibles et d’absence de calibration sont historiques. Voir [MODELE_VIDEO_CALIBRATION.md](MODELE_VIDEO_CALIBRATION.md).

# Audit des deux prompts — 8 novembre 2026

Audit de la branche `main` au commit `018157e11f1e610227931e8ee801d66c9a8e7afb`,
puis des changements du protocole expert. Aucun moteur LLM ni chargement de
prompts conversationnels n'a été trouvé dans les modules de conseil. Les règles
exécutées sont du Python ; enregistrer les deux textes bruts n'aurait pas changé
le comportement du logiciel.

## Conflits et résolution

| Directive reçue | Où elle entre en conflit | Résolution appliquée |
|---|---|---|
| Do = 5, Soin = 5, Prospe = 5, PP = 0,1 | `Application/forgely_dofocus.py`, ancien `FAMILIES` ; nouvelle table `Application/references/poids_runes_client_3_7_13_17.json` | Dommages génériques 20 ; dommages élémentaires 5 ; Soins 10 ; Prospection 3. PP n'est pas une caractéristique distincte ; aucune valeur 0,1 attribuée à la prospection. Les valeurs déjà correctes du moteur sont conservées. |
| Poids « immuables », connus absolument | `Application/forgely_connaissances.py`, divergences des guides ; `Application/forgely_weights.py` | Un référentiel client versionné, avec provenance non certifiée éditeur et empreintes. Ni Rétro ni Touch ni serveur alternatif. |
| Une formule du puits appliquée à chaque pose | `Application/forgely_decision.py::pool_transition` | SC conserve le puits. SN/EC : max(0, puits + pertes − rune). L'audit ne certifie le total que sur données complètes. Une perte sur la ligne ciblée tient compte du gain nominal en SN. |
| Puits « Max 101 », affichage x/100 | `Application/forgely_rules.py::constraints` et `pool_transition` | 101 reste un garde-fou distinct de densité, pas un plafond du reliquat. Aucun écrêtage du puits à 101. |
| Over/exo uniquement avec puits suffisant | `Application/tests/test_decision.py::test_cap`, `::test_exo_reference_separate` ; moteur `candidates` | Aucune obligation générale de puits pour exo. Le puits mesure l'exposition ; il ne garantit aucun SC. |
| Quatre phases rigides et destruction volontaire de lignes lourdes | `Application/forgely_decision.py::candidates`, objectifs utilisateurs | Pas de sacrifice automatique. Priorité désormais explicite à une remontée naturelle ciblée disponible avant over/exo. L'ordre des autres lignes reste un classement heuristique. |
| Remonter toutes les grosses lignes au maximum | `Application/forgely_plan.py::save_plan`, `advise` | Les cibles saisies sont des minima. Une ligne non ciblée n'est pas implicitement exigée au maximum. |
| Arrêt à 98 % ou si un risque dépasse 60 % | `Application/forgely_decision.py::advise` ; `Application/forgely_copilote.py::goal_reached` | Aucun seuil arbitraire. Arrêt à toutes les cibles atteintes ou au budget épuisé. Une finition identifiée provoque une alerte de risque qualitatif, pas une probabilité inventée. |
| Prochaine rune fixe après SN/EC et puits Y/Z prédits | `Application/forgely.py::strategy_current`, lecture après fusion | Relecture confirmée obligatoire. SC : une branche hypothétique calculée sans perte ; SN/EC : formule conditionnelle sans nombre ni rune de secours inventés. |
| Identifier « mauvaise chance » ou saturation après un seul échec | `Application/forgely_labo_live.py::compute_snapshot` | Aucun diagnostic causal individuel et aucun coefficient serveur déduit d'une série d'EC. |
| Pourcentage de confiance et probabilité finale à chaque tour | `Application/forgely_decision.py`, `goal_probability=None` | Probabilité d'atteinte future et confiance chiffrée restent non estimées. L'objectif déjà atteint est un état constaté, pas une prédiction. |
| RL instantané, MCTS, A*, théorie des jeux | `Application/forgely_fm_model.py`, `Application/forgely_labo_live.py`, `Application/forgely.py::strategy_current` | Ces algorithmes ne sont pas implémentés. Le tableau explicite un classement heuristique ; il ne les prétend pas actifs. |
| Mélange 40 % simulations / 60 % réel évoqué auparavant | Même moteur et laboratoire ; aucun module d'entraînement/politique découvert dans l'arbre du dépôt audité | Absent de cette branche. Les observations restent descriptives ; les simulations restent distinctes. Cette pondération n'est ni ajoutée silencieusement ni prétendue existante. |
| Maximiser la revente de l'objet | `Application/forgely_tools.py`, prix disponibles des runes uniquement | Objectif du jet demandé puis économie des runes. Pas d'estimation de prix de revente de l'objet ni de bénéfice promis. |
| Autonomie à 100 % dans le jeu | `Application/forgely.py`, architecture d'observation passive | Analyse et conseil autonomes ; aucune pose ou entrée automatique dans DOFUS. |

## Incohérences internes trouvées

1. `Application/forgely_probabilites.py::BASE` et
   `Application/forgely_dofocus.py::FAMILIES` étaient deux tables distinctes.
   La première excluait notamment certaines runes de retrait/esquive, que l'autre
   traitait. `BASE` dérive maintenant de la table commune ; il n'y a plus deux
   définitions concurrentes de la densité utilisée.
2. Onze entrées parmi les 105 prix/icônes n'avaient pas de référence dans
   l'ancien moteur de décision. Neuf runes ordinaires et Chasse ont désormais
   leur poids ; Signature reste explicitement hors combat. Les variantes Ra de
   poussée et les familles de dommages/résistances mêlée/distance sont reliées
   au catalogue. La liste des choix n'est plus construite en supposant qu'une
   variante a nécessairement le même multiplicateur qu'une autre famille.
3. `docs/REFERENCE_DOFOCUS.md` et l'en-tête de `forgely_rules.py` attribuaient
   encore l'ensemble du référentiel à Dofocus. Les densités viennent maintenant
   de l'extraction client ; Dofocus reste uniquement une source distincte de
   relevés de simulation pour des états exacts. La documentation est actualisée.
4. Le moteur pénalisait seulement les finitions pendant une remontée naturelle.
   La priorité est maintenant un filtre de classement dans les deux modes,
   lorsqu'une rune naturelle ciblée est disponible après les contrôles de coût,
   de budget et de légalité. Un exo bon marché ne passe plus devant elle.

## Vérification des sources des poids

Les pages Ankama essayées (encyclopédie Ga Pa et Vi, ancien devblog, notes de
mise à jour) ont été inaccessibles depuis cet environnement, notamment HTTP 403.
Aucune table exhaustive directement publiée par Ankama n'a été vérifiée.

Le référentiel livré est dérivé des fichiers `itemsdata.json` et
`effectsdata.json` de la release tierce dofus-sqlite `v6.0_3.7.13.17`, vérifiée
par SHA-256. Les identifiants et noms sont associés au catalogue de runes déjà
présent dans Forgely et aux captures utilisateur. Les effets proviennent des
classes `Ankama.Dofus.Core.DataCenter`. Cela reste une extraction indépendante,
sans certification officielle de l'éditeur. Les réponses exploratoires de
DofusDB ne sont pas incluses dans le référentiel livré.

Le poids d'inventaire `realWeight` n'est jamais utilisé pour la FM. Le gain vient
de l'effet de la rune ; le coefficient vient de `EffectData.effectPowerRate`.
La valeur brute float32 est conservée, et la valeur numérique est arrondie à six
décimales avant multiplication.

Exemples désormais couverts : Do Ren 5, Pa Do Ren 15, Ra Do Pou +10 / poids 50,
Ré Per Mé et Ré Per Di 10 par point. Ces entrées manquaient auparavant au moteur ;
les densités des 94 entrées déjà connues n'ont pas changé. Signature n'est jamais
convertie en une rune gratuite de poids 0.

## Règles historiques et limites conservées

`Application/reference_poids_fm.csv` reste une archive documentaire indicative,
étiquetée non certifiée DOFUS 3 ; elle ne pilote pas le conseil. Le fichier nommé
`catalogue_runes_officiel.csv` contient des identifiants/noms/icônes : son nom
n'est pas une preuve de certification des poids par Ankama.

Le module documentaire `forgely_huzounet` conserve des hypothèses communautaires,
dont le cas particulier des exos lourds. Le conseiller actif n'en déduit pas un
taux fixe pour toutes les poses. Les relevés Dofocus exacts peuvent déjà pondérer
le classement par leur somme SC+SN affichée ; cela n'est pas un apprentissage
40/60 et ne valide pas ces valeurs comme des probabilités du jeu.

Le contrôle des malus et des transcendances reste hors du moteur ordinaire.
L'import des prix et ce protocole ne modifient ni les observations ni les
statistiques d'entraînement. Les tests Windows natifs restent à effectuer sur
la machine de l'utilisateur.

## Validation de cette mise à jour

- 466 tests réussis, 16 ignorés, 25 sous-tests réussis.
- 146 fichiers Python compilés sans erreur.
- Relecture indépendante du protocole et des poids : aucun défaut bloquant trouvé.
- Paquet local testé sur les sources des commits `b6e3dce` et `018157e` :
  sauvegarde, 12 fichiers installés, second passage sans réapplication et données
  utilisateur inchangées. Une version locale différente reste refusée.
- Aucun lancement natif Windows ou test du nouvel EXE n'a été réalisé ici.
