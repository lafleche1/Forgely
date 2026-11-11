# Corrections : puits, apprentissage et sélecteur final

## Périmètre

Modifications du dossier local v22.16 suite à l'audit GitHub. Ce dossier n'a pas
de métadonnées Git. Les empreintes et sauvegardes remplacent une référence de
commit local ; elles ne prouvent pas une publication sur GitHub. Une autre
intervention locale harmonise simultanément le modèle de probabilités et les
transitions empiriques : ses changements sont conservés, sans rétablir l'ancien
modèle à leur place.

## Comportements corrigés

- Les objectifs mesurés et le plan enregistré utilisent le même fournisseur de
  sources d'apprentissage. Le nom doit être confirmé, le snapshot stable et le
  profil compatible pour utiliser les entraînements propres à un équipement.
  Sans identité, le conseil reste possible sur les lectures mais n'emprunte
  aucune statistique d'un objet supposé.
- La phase de puits exprime une préférence parmi les runes déjà autorisées.
  Sans rune préférée, repli sur les candidats légaux ; aucune cible inventée.
  Ainsi, un PA/PM naturel ciblé peut être restauré avec un puits insuffisant.
- Puits 1–5 : préférence conservatrice pour les petites runes. Le poids non
  couvert est une exposition. Le compteur atteignant zéro n'est jamais présenté
  comme un gain de poids gratuit. Les over/exos exigent une cible explicite.
- La trace distingue score heuristique, ajustement des sources, éventuelle
  substitution par un score de séquence, économie, phase et rang final. Le 60/40
  s'applique à un ajustement, pas nécessairement à toutes les étapes du choix.
- Toutes les politiques exigent désormais un audit du sélecteur final, avec
  version, empreinte du code, paramètres économiques et contenu de la politique
  (Q et visites compris). Les résultats périmés ne suffisent plus. Toute
  invalidation vide le cache de tous les états, pas seulement l'état affiché.

## Audit indépendant

`Application/auditer_politique.py --selector` évalue le conseil final avec et
sans une politique figée sur des graines indépendantes de l'apprentissage.
Il utilise le budget d'essais du worker déployé, les séquences et la matrice.
Il n'écrit ni observation joueur, ni drapeau d'activation dans le checkpoint.
Les résultats restent des simulations du modèle local.

Le test initial sur une petite configuration a donné 41/50 réussites par bras,
sans amélioration ni influence apprise effective dans ce cas à une seule action.
Il s'agit d'un contrôle fonctionnel, pas d'une validation des performances sur
un objet complexe. L'empreinte a ensuite changé pendant l'harmonisation : ce
résultat initial doit être remplacé par l'audit de l'état final.

## Historique des recommandations : demande complémentaire

L'utilisateur a précisé supprimer l'historique enregistré, sans retirer les
règles ni les entraînements. La purge du vrai profil Windows a retiré **221
éléments de recommandations** du journal virtuel. Les **5 observations réelles**
et les mesures des **111 simulations** sont inchangées, vérifiées par empreintes
avant/après (`history-removal.json`). Aucun ancien conseil n'est conservé dans
une sauvegarde de données par cette opération.

Les prévisions d'une session restent en mémoire pour comparer le résultat
réellement observé, puis sont libérées. Elles ne sont plus écrites dans la table
des anciennes prévisions ni dans les fichiers de bilan. Le journal virtuel
conserve uniquement les mesures, pas les décisions de séquence ni les facteurs
de politique. Les bilans gardent les tentatives et les métriques agrégées.

La prévision continue de partir du jet/puits/rune/pertes/résultats visuellement
lus et confirmés, avec les objectifs, règles, poids, modèles, simulations et
entraînements validés déjà implémentés. L'historique des conseils n'est jamais
une vérité d'apprentissage. Un test injecte une ancienne recommandation et
vérifie que le modèle empirique et la calibration ne la prennent pas en compte.

## Vérification finale

Les nouveaux tests ont été exécutés avant correction et ont reproduit les
blocages puis vérifiés après correction. Résultat final : **1730 tests passés,
26 ignorés, 42 sous-tests passés, aucun échec**, en73,86s. Suite complète avec
TEMP/TMP dans le workspace et Tesseract installé ajouté au PATH du processus.
Le test de désaccord compare maintenant une source active et une différence
effective ; il n'impose pas le taux historique d'un autre modèle.

Compilation Python réussie ; autotest de l'entrée de l'entraîneur réussi.
Deux revues indépendantes ont vérifié intégration et suppression de l'historique,
sans défaut bloquant restant. Les sorties intermédiaires et leurs anciens
échecs ne remplacent pas ce résultat final (`tests.log`, `tests.xml`).
Aucune validation de performance en jeu ni de délai OCR dans DOFUS n'est déduite
de ces vérifications hors jeu.

Audit final : `selector-user-runtime-audit.json`, 50 épisodes par bras sur l'objet
77, cible Force13, horizon8. **16/50** jets complets dans chaque bras ; aucun
changement de choix, aucun facteur appris applicable dans ce cas à une action.
Ce contrôle du sélecteur réel utilise les préférences du vrai profil Windows.
L'empreinte du code et celle des réglages correspondent à l'état livré.
Ce n'est pas un benchmark représentatif de toute la FM. La supériorité n'est pas
démontrée : **aucune politique activée**.

`selector-final-audit.json` est conservé comme résultat **intermédiaire périmé** :
ancien classement sur Force23/horizon8, 800 conseils dont196 avec facteur appris,
0/50 par bras. Le classement a depuis été aligné sur les probabilités du modèle
partagé. Cet ancien audit ne valide pas le code final et ne doit pas être fusionné
avec le contrôle final. `selector-audit.json` est aussi un contrôle antérieur.

Le classement et l'affichage utilisent désormais la même prédiction du modèle
partagé, avec niveau et calibration du contexte connus. Les anciennes bandes
fixes ne guident plus le classement actif. L'API historique reste disponible
pour compatibilité, sans être consommée par le sélecteur actif.

Le mélange 60/40 reste un ajustement des sources lorsqu'il s'applique. Un
posterior partagé déjà calibré utilise son poids réel n/(200+n), sans second
ajustement des mêmes résultats. La trace expose les sources effectivement
appliquées et celles supprimées pour éviter le double comptage.

Pour charger les sources corrigées, utiliser `LANCER_FORGELY_MIS_A_JOUR.bat` et,
pour l'entraîneur, `LANCER_ENTRAINEMENT_MIS_A_JOUR.bat`. Les anciens exécutables
autonomes ne sont pas remplacés par cette intervention. Aucun push GitHub.

Sauvegardes : `before/`. Plan : `PLAN.md`. Tests : `tests.log` et `tests.xml`.
L'API historique de classification, supprimée lors de l'harmonisation parallèle,
est conservée dans `forgely_fm_classification.py` et réexportée par le nouveau
modèle ; elle provient du fichier GitHub au commit 71b40277.
