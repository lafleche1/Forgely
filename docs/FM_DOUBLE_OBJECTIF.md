# Deux modes de recommandation

Dans « Détail de la recommandation », sélectionner **Chances maximales** ou
**Budget optimisé**. Le choix est conservé. Les deux modes utilisent les mêmes
lectures confirmées, objectifs et contraintes de forgemagie.

| Mode | Critères du classement |
| --- | --- |
| Chances maximales | Progression vers la cible, palier simple/Pa/Ra, équilibre des lignes et exposition faute de puits ; différer les finitions fragiles lorsque des lignes naturelles ciblées restent à remonter. |
| Budget optimisé | Même base de règles, progression rapportée au prix saisi, pénalité indicative pour la réparation lorsque du poids n'est pas couvert par le puits. |

Il s'agit de **classements heuristiques**, pas d'une formule officielle ni d'une
preuve d'optimalité. Aucun taux de réussite final n'est inventé. Les observations
agrégées restent descriptives ; les fréquences OCR du laboratoire sont séparées
par valeurs exactes du jet observé et classe de puits, et restent exploratoires.

## Prix et dépenses

Renseigner les prix locaux dans « Prix et budget de cette session » ou « Outils →
Stratégie et kamas ». Les deux écrans partagent les mêmes préférences.
Un prix absent reste inconnu. Le mode économique ne propose que des runes dont le
prix est renseigné. Avec un budget limité, les deux modes écartent les runes dont
le prix est inconnu ou dépasse le montant restant.

Le budget s'applique aux tentatives **enregistrées depuis le lancement de Forgely,
tous objets confondus**. Les observations antérieures sont exclues. Le montant est
recalculé aux prix actuellement saisis ; ce n'est ni un solde d'inventaire ni une
garantie que toutes les poses ont été capturées. Redémarrer ouvre une nouvelle
session. La valeur 0 dans les préférences signifie « sans limite » ; un budget
restant calculé à 0 impose l'arrêt. Si des tentatives enregistrées n'ont pas de
prix, le conseil sous budget est suspendu jusqu'à la saisie de ces prix. Les
tentatives détectées sans rune identifiable sont également comptées comme
dépenses inconnues : leur présence empêche de certifier le budget de la session.

## Règles et limites

- Poids et familles de runes partagés entre contraintes et classement.
- Over : contrôle de la densité totale de la ligne, pas seulement du surplus.
- Exos : contrôle de la densité cumulée des lignes exotiques lorsque le profil
  naturel complet est fourni au moteur.
- Les profils CSV importés dans l'application restent considérés comme partiels :
  une ligne absente du CSV ne prouve jamais que la rune est exotique.
- Un petit dépassement de la cible est autorisé uniquement s'il reste dans une
  borne naturelle connue ; pas d'over involontaire pour combler un petit écart.
- Les malus et transcendances ne sont pas proposés par le moteur ordinaire.
- Après fusion, attendre la confirmation du jet ; objectif atteint : arrêt conseillé.

Références communautaires vérifiées le 7 novembre 2026 :
[Huzounet](https://huzounet.fr/guides/forgemagie),
[Gamosaurus](https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus).
Les divergences de tables de runes restent explicites dans `forgely_connaissances.py`.
Ce modèle vise DOFUS PC ; ne pas transposer à Rétro, Touch ou un serveur alternatif.

## Comparaison avec le moteur précédent

Scénarios déterministes couverts par les tests, sans simulation des probabilités du jeu :

| Situation | Avant | Après |
| --- | --- | --- |
| Force 101, maximum naturel 100, cible 102 | Contrôle du seul surplus : rune proposée | Refus du dépassement de densité totale de ligne |
| Cible +10 Force, Fo à 1 K, Pa Fo à 100 K, Ra Fo à 10 000 K | Prix ignorés, Ra Fo | Mode économique : Fo ; mode chances : Ra Fo |
| Vi 299, cible 300, maximum naturel 350 | Aucune rune car gain minimal supérieur à l'écart | Vi autorisée sans dépasser le maximum naturel |
| Même objet, mêmes lignes, valeurs de Force 10 et 99 | Fréquences mélangées | Groupes séparés |

Ces améliorations de comportement ne mesurent pas une hausse de réussite réelle.
Pour mesurer ce gain : comparer des sessions avec mêmes objets, jets initiaux,
cibles et budgets, puis relever le taux d'atteinte de la cible et le coût total
incluant les remontages. Éviter de valider le moteur sur ses propres simulations.

Tests : `python -m pytest -q`. Les tests graphiques nécessitent un affichage et
`FORGELY_GUI_TESTS=1` ; l'OCR et la capture Windows doivent être vérifiés en jeu.
