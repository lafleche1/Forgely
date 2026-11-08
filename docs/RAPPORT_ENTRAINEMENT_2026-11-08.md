# Rapport local — Forgely-Entraînement, 8 novembre 2026

Travail réalisé exclusivement dans la copie locale. Aucune publication GitHub.

## Conclusion mesurée

Les défauts de curriculum, de reprise et de cohérence des actions sont corrigés.
L'expérience ne démontre pas que la politique apprise est supérieure au témoin.
Elle reste **inactive dans les conseils**. Aucun gain dans DOFUS n'est démontré.

## Diagnostic et corrections

- **Zéro entraînement ciblé** : l'ancien code attendait la moitié de l'horizon
  (2 500 poses pour une limite de 5 000), souvent après la fin de l'épisode.
  Un échantillonnage en réservoir capture maintenant un état de chaque épisode
  échoué, même court. Un quart des épisodes peut repartir du tampon (64 états).
  Le rejeu conserve l'horizon restant, sans alimenter l'évaluation.
- **Blocages sur des cibles minimales** : le succès acceptait `valeur >= cible`,
  mais les actions interdisaient tout dépassement. Exemple : Vitalité 289,
  cible minimale 290, maximum naturel 300 ; la rune Vi était refusée.
  L'environnement accepte maintenant ce surplus naturel, comme le copilote.
  Les over/exos non demandés restent exclus.
- **Remplacement par la dernière politique** : les archives sont conservées et
  la reprise sélectionne la validation puis la borne basse Wilson de réussite
  du jet complet, sans prix ni nombre de runes dans ce classement.
  Le chargeur du copilote conserve les champions compatibles avant d'appliquer
  sa limite mémoire ; plus de priorité aveugle aux 1 000 dernières archives.
- **Évaluations trop petites** : 200 sessions par défaut dans le moteur et
  l'interface, jusqu'à 1 000 configurables. Un petit essai de diagnostic demeure
  possible ; moins de 50 sessions ne peut pas valider une politique.
- **Reproductibilité** : graines dérivées par SHA-256 avec domaines distincts
  pour apprentissage, sélection et audit. Le curseur avance même si une
  candidature moins bonne est rejetée. Les deux stratégies reçoivent les mêmes
  graines dans chaque comparaison. La politique est figée pendant les essais.
- **Compatibilité** : nouvelle version `tabular-no-currency-4` ; anciennes
  politiques conservées, sans reprise ou influence automatique avec ces règles.

## Probabilités et intégration au copilote

L'entraîneur et le copilote utilisent `forgely_dofocus_engine.odds` pour SC/SN/EC.
L'entraîneur échantillonne des transitions avec `attempt`. Le copilote combine
modèle local, essais virtuels et éventuellement observations comparables.
La politique Q ajoute un facteur de classement borné, pas une probabilité.

La récompense existante donne priorité à toutes les cibles atteintes
simultanément, sans prix des runes ; ces propriétés sont vérifiées par tests.
La politique n'est chargée dans les conseils qu'après validation de sa
supériorité sur les jets complets (intervalles Wilson à 95 % disjoints).
Son facteur touche uniquement la contribution simulation. Lorsque les deux
sources sont exploitables : **60 % réel / 40 % simulation**. En l'absence de
réel exploitable, le repli simulation seule est explicitement identifié ;
aucune observation réelle n'est fabriquée et aucun 60 % réel n'est revendiqué.

## Expérience reproductible

Objet : Anneau du Cycloïde (14092), mêmes cibles que le rapport signalé.
100 épisodes nouveaux, sans reprise ; horizon limité à **200 poses**, puis
200 évaluations par stratégie. Ce choix diffère de la limite historique de
5 000 poses : les résultats ne constituent pas une comparaison directe avec
les anciens 3/20 et 5/20.

Graine d'apprentissage/sélection : 20261107. Audit séparé : 20261108, domaine
`independent_audit`. L'audit ne modifie ni la politique ni son activation.

| Mesure | Politique apprise | Témoin |
|---|---:|---:|
| Jets complets, banc de sélection | 171/200 | 161/200 |
| Poses moyennes, sélection | 102.595 | 107.505 |
| Jets complets, audit indépendant | 170/200 | 167/200 |
| Poses moyennes, audit | 104.82 | 102.73 |

**22 épisodes ciblés** réalisés ;
35 états en tampon. Aucun abandon faute
 de rune admissible pendant les 200 évaluations de chaque stratégie dans
cette expérience corrigée (les épisodes peuvent atteindre la limite de poses).

Audit : réussite apprise 85 %, intervalle Wilson 95 % [79,39 % ; 89,29 %] ;
témoin 83,5 %, intervalle [77,73 % ; 88,00 %]. Les intervalles se recouvrent.
**Amélioration non démontrée ; activation refusée.** Les poses moyennes restent
une information descriptive, jamais un objectif monétaire ou un critère de promotion.

Résultats détaillés : `training-fix-experiment-2026-11-08.json`.
Configuration : `training-reproduction-config-2026-11-08.json`.
Archive : `Entrainements/verification-20261108/20261108-021833-877007-14092-5ff083/policy.json`.
SHA-256 de la politique auditée : `2c200d7f25b9ec67a866ae42e8bf1720b52db61ee36cfa3021b60e8b2037db7b`.

Pour reproduire l'audit depuis la racine locale, dans PowerShell :

```powershell
.venv/Scripts/python.exe Application/auditer_politique.py Entrainements/verification-20261108/20261108-021833-877007-14092-5ff083/policy.json --episodes 200 --seed 20261108 --output docs/audit-reproduit.json
```

Pour refaire l'entraînement, utiliser les valeurs du JSON de configuration
(la fenêtre permet 100 sessions, 200 poses, 200 vérifications, sans reprise).
La configuration complète et la graine sont sauvegardées avec chaque politique.

## Vérification et livraison

- **796 tests de domaine réussis** : apprentissage, curriculum, reprise,
  archives, reproductibilité, moteur SC/SN/EC, récompense, absence de monnaie,
  pondération, intégration des conseils, interface d'entraînement.
- Suite générale finale : **1 480 réussis, 26 ignorés, 1 échec**, plus 42 sous-tests
  réussis. Le test en échec est `test_manual_object_and_saved_goal_reach_advice_on_third_fresh_reading` dans
  `Tests/test_manual_goal_advice_flow.py`. Il échoue dans la suite et passe
  exécuté seul (1 réussi). Sa cause globale n'est pas établie ici ; ce point
  reste ouvert. La suite complète n'est donc pas déclarée verte.
- Les premiers essais ont rencontré des restrictions des dossiers temporaires
  Windows ; la vérification générale a ensuite été exécutée avec l'accès requis.
  Le chemin de Tesseract déjà installé a été ajouté au processus de test.
- `Entrainement_Forgely.exe` reconstruit localement ; son autotest exécute et
  sauvegarde deux épisodes et confirme la nouvelle version de politique.
  SHA-256 : `55a6af6915b1f3e0c939275c17190eec14759a412a457bb1e35424fd12fbd2d5`.
- Vérification de compilation des cinq fichiers applicatifs modifiés : réussie.
- Relecture indépendante : défaut de priorité aux archives récentes détecté,
  corrigé et couvert par un test avec 1 000 archives plus récentes ; relecture
  finale sans autre défaut important identifié.

Sources modifiées : `forgely_training.py`, `forgely_rl.py`,
`forgely_trained_policy.py`, `entrainer_forgely.py` ; ajout de
`auditer_politique.py`. Tests ajoutés/étendus dans `test_training_regressions.py`
et `test_trained_policy_advice.py`. Les sources du copilote local sont utilisées
par le lanceur habituel `OUVRIR FORGELY.bat`.

## Limites à conserver

Le modèle local reproduit des mécanismes observés de Dofocus ; il ne prouve
pas les probabilités officielles du jeu. L'état tabulaire discrétisé laisse
beaucoup d'états jamais appris ; 100 épisodes ne prouvent pas une couverture
suffisante. Le facteur Q du copilote est un ajustement du classement hybride :
la validation de la politique seule n'est pas une mesure de gain du copilote
hybride en conditions réelles. Le banc fixe sert à sélectionner les archives ;
répéter cette sélection ne remplace pas un audit indépendant. Le chargement
parcourt les archives en arrière-plan et conserve au plus 64 Mio : beaucoup
d'archives accroissent le temps de lecture et des configurations moins bien
classées peuvent être absentes lorsque cette capacité est dépassée.


Note de suivi : ce rapport décrit la première livraison de la journée. L'exécutable
courant a ensuite été remplacé par la version 5, dont l'option de recherche
généralisable est expérimentale et décochée. Voir le
[rapport de la seconde campagne](RAPPORT_GENERALISATION_2026-11-08.md) pour
l'audit à 1 000 sessions, le résultat négatif et l'empreinte actuelle de l'exécutable.
