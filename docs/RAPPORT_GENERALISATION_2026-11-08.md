# Apprentissage généralisable — rapport du 8 novembre 2026

## Résultat et usage

Le seuil conservateur de supériorité sur le témoin n’est pas atteint pour la politique directe.
**Aucune amélioration du copilote final ou dans DOFUS n'est démontrée par cet audit.**
La nouvelle politique reste expérimentale et inactive dans les conseils.
L'option correspondante est décochée par défaut : la stratégie mesurée moins
performante n'est pas imposée aux futurs entraînements.
Aucun candidat n'a été choisi ou retouché après consultation de l'audit final.

## Modifications livrées localement

- Nouvelle politique compacte : elle classe les actions à partir de la progression
  en masse, du déficit restant, de l'exposition après reliquat et du surplus naturel.
  Contrairement à une table d'états, elle produit des scores sur des situations inédites.
- Apprentissage de la stratégie par tournoi entre huit jeux de paramètres et la
  table existante. Chaque candidat reçoit les mêmes graines et les mêmes départs
  difficiles. Seule la réussite simultanée de toutes les cibles départage les candidats ;
  ni prix, ni budget, ni consommation de runes dans ce critère. En cas d'égalité,
  la table garde la priorité.
- Option expérimentale décochée par défaut après l'audit négatif. Lorsqu'elle
  est demandée, sa recherche est bornée à 256 trajectoires, arrondie pour
  répartir équitablement le budget ; elle n'est lancée que pour des entraînements
  d'au moins 32 sessions et son volume ne dépasse pas celui de l'entraînement principal.
  L'interface et le rapport affichent ce travail supplémentaire séparément.
- Les départs difficiles conservent le reliquat, les lignes et l'horizon restant.
  Les graines de recherche restent distinctes des évaluations et de l'audit final.
- L'auditeur prend en charge les nouvelles politiques et les archives de version 4,
  avec vérification de compatibilité et d'empreinte ; un modèle compact corrompu
  ne peut pas être audité silencieusement comme une autre stratégie tabulaire.
- Chargement préparé pour des scores généralisés sans inventer des visites de
  cet état ou des observations de joueurs. La pondération existante 60 % réel /
  40 % simulation est conservée lorsque les deux sources sont exploitables.
- Protection d'activation renforcée : le test d'une politique directe ne certifie
  pas le classement combiné du copilote. Pour une politique compacte, le chargeur
  exige un audit du sélecteur réellement utilisé, lié à l'empreinte des paramètres,
  du profil, de la configuration et des versions. Aucun tel audit n'a été fabriqué.

Version nouvelle : `generalized-no-currency-5`. Les archives précédentes restent
conservées ; elles ne sont pas réinterprétées comme des politiques de cette version.

## Campagne exécutée

Même Anneau du Cycloïde (14092) et mêmes cibles que la première campagne ; horizon
200 poses, départ moyen et reliquat nul. Cette configuration ne permet aucune
conclusion générale sur tous les objets ni sur la limite historique de 5 000 poses.

- 1024 sessions d'apprentissage tabulaire, dont
  253 replays de difficultés.
- 50000 états mémorisés : limite de capacité atteinte, ce qui confirme
  qu'une simple augmentation de cette table laisse des états non appris.
- 252 trajectoires supplémentaires de recherche,
  soit 28 par candidat, dont
  63 départs difficiles répartis entre candidats.
- Paramètres retenus dans la campagne expérimentale : [1.0, 0.0, 1.0, 0.0].
- Première vérification de développement : 172/200
  contre 161/200. Elle n'a pas servi à changer
  les paramètres retenus ; le candidat a été figé avant le lot final.

## Audit final indépendant

Graine **20261110**, domaine `independent_audit`, 1 000 épisodes par stratégie,
identiques entre stratégies. La politique et le témoin n'apprennent pas pendant
cet audit. Le témoin a été recalculé avec chaque archive et donne les mêmes résultats.
Les poses sont uniquement un indicateur descriptif.

| Stratégie | Jets complets | Réussite | Poses moyennes | Intervalle Wilson 95 % |
|---|---:|---:|---:|---:|
| Nouvelle politique compacte | 834/1000 | 83.4 % | 107.14 | 80.97–85.58 % |
| Ancienne politique tabulaire (100 sessions) | 840/1000 | 84.0 % | 102.64 | 81.60–86.14 % |
| Témoin heuristique | 860/1000 | 86.0 % | 102.60 | 83.71–88.01 % |

Le critère de validation demeure inchangé : la borne basse Wilson à 95 % de la
politique doit dépasser la borne haute du témoin. Il n'a pas été assoupli pour
obtenir une activation. La comparaison de l'ancienne politique utilise également
ces nouveaux tirages ; elle ne reprend pas simplement ses anciens 170/200.

SHA-256 de la nouvelle archive figée : `02490e96b310266161e683e9de310c9a0779de74e9d336507b1845a7772dedfe`.
Aucune promotion dans le dossier d'activation du copilote n'a été effectuée.
L'archive de recherche est dans `Entrainements\recherche-generalisation-20261108\20261108-023450-692842-14092-bfa388\policy.json`.

Résultats : `general-policy-development-2026-11-08.json` et
`general-policy-final-audit-2026-11-08.json`.
Configuration : `general-policy-reproduction-config.json`.

Pour reproduire l'audit depuis la racine du projet, dans PowerShell :

```powershell
.venv/Scripts/python.exe Application/auditer_politique.py Entrainements/recherche-generalisation-20261108/20261108-023450-692842-14092-bfa388/policy.json --episodes 1000 --seed 20261110 --output docs/audit-general-reproduit.json
```

## Ce qui n'est pas établi

Les scores compacts sont des utilités de classement, pas de nouvelles probabilités
SC/SN/EC. Le même modèle local Dofocus fournit toujours ces probabilités. Aucune
calibration réelle n'a été ajoutée : la base locale lue en mode non modifiant ne
contient que 2 observations `ocr_confirmed` et 3 `ocr_auto`, insuffisantes pour
valider des transitions contextuelles. Aucun taux officiel du jeu n'est revendiqué.

L'optimisation sur des trajectoires complètes tient indirectement compte des
pertes et réparations ; ce n'est pas une nouvelle recherche exhaustive de séquences
à chaque pose. Le choix parmi huit fonctions reste une famille de stratégies limitée.

Le copilote applique ensuite une matrice de priorité par phase de puits et des
calculs de séquences. Ses décisions peuvent différer de l'argmax de la politique
entraînée. Cet audit final porte sur la politique directe, **pas sur ce sélecteur
complet avec données réelles**. Pour cette raison, même un éventuel gain direct ne
déclenche pas à lui seul une activation des conseils. Le travail de validation
complète du copilote demeure à réaliser.

## Tests et exécutable

- 64 tests ciblés d'apprentissage, chargement, validation et interface
  réussis, plus 752 tests du moteur, de l'environnement et des simulations réussis.
- Suite générale exécutée : 1493 réussis, 26 ignorés, 1 échec ; 42 sous-tests réussis.
  Échec : `test_manual_object_and_saved_goal_reach_advice_on_third_fresh_reading`, dans
  `Tests/test_manual_goal_advice_flow.py`, déjà observé avant cette seconde phase.
  La suite générale n'est pas annoncée entièrement verte.
- Relecture indépendante : séparation formation/évaluation et sérialisation
  vérifiées ; écart de validation du sélecteur identifié puis couvert par le garde
  et les tests de refus. Aucun autre défaut important signalé à la relecture finale.
- `Entrainement_Forgely.exe` reconstruit ; autotest de la version 5 et compilation
  des modules modifiés réussis.
  SHA-256 de l'exécutable : `73429b6a312594957d158b79aa0be74c2de5f59867ce3a45e782d7a554b75f24`.

Sources : ajout de `forgely_general_policy.py` ; mises à jour de
`forgely_training.py`, `forgely_trained_policy.py`, `auditer_politique.py` et
`entrainer_forgely.py`. Ajout de tests de généralisation, d'annulation, de
reproductibilité, de refus d'activation et du calcul des conseils sur état inédit.

Aucun changement publié sur GitHub et aucune observation réelle modifiée.
