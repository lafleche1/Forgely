# Analyse de la session Tétriste et de la méthode proposée

Vidéo fournie : 67.2 secondes, 30 images/s, 1918 × 1078. Analyse locale, sans
action dans le jeu. La session est fournie par l'utilisateur comme celle de
l'Amulette Tétriste ; les quatre caractéristiques et la Portée sont suivies.
135 images ont été échantillonnées à 0.5 s. Seize transitions ont ensuite été
vérifiées visuellement avec les états, stocks/runes et dernières lignes du
journal. Les états incomplets ou les intervalles ambigus ne sont pas complétés.

Les annotations sont conservées dans
`work/session_malus_20261110/verified_transitions.json` avec l'empreinte SHA-256
de la vidéo et les images `proof_*.png`. Ce sont des preuves d'analyse vidéo,
pas des observations automatiquement importées dans l'apprentissage ou les
statistiques réelles de Forgely.

## Observations les plus utiles

| Intervalle vidéo | Pose identifiée | Changements lus | Puits lu | Conclusion étayée |
|---|---|---|---|---|
| 4.5–5.5 s | Pa Cha | Chance -12→-9 ; Force +1→0 | 37→36.5 | Perte positive de 1 et consommation de 0.5 : coût total de pose de 1.5. |
| 6.5–7 s | Pa Cha | Chance -9→-6 ; Force 0→-3 | 36.5→36.5 | Les pertes en négatif absorbent le coût sans diminution du puits. Le poids 0.5/point explique ce cas. |
| 10.5–11.5 s | Pa Cha | Chance -3→0 ; Force -9→-15 | 36.5→36.5 | Avec les six points perdus à demi-poids, cette pose atteignant zéro coûte 3, pas 1.5. |
| 12–13 s | Pa Age, sans gain | Chance 0→-3 | 36.5→36.5 | Une ligne déjà annulée peut redevenir négative malgré un puits disponible. |
| 19–19.5 s | Ra Fo | Force -12→-2 ; Chance -12→-15 ; Agilité -9→-15 | 36.5→36 | Neuf points négatifs perdus à demi-poids, plus 0.5 de puits, expliquent un coût de pose de 5. |
| 23.5–24.5 s | Ra Age | Agilité -15→-5 ; pas d'autre changement | 32.5→27.5 | Coût de 5 directement visible en puits, sans devoir estimer une perte. |
| 25.5–26 s | Ra Ine | Intelligence -15→-5 ; Agilité -5→-15 | 27.5→27.5 | Dégradation d'un malus remonté alors que le puits est encore disponible. |
| 50.5–51 s | Ra Cha | Chance -5→0, gain affiché +5 | 0→0 | La pose observée ne donne que les cinq points restants jusqu'à zéro. Aucun coût de SN/EC de ce franchissement ne peut être mesuré sur cette réussite sans perte. |
| 59.5–60.5 s | Ra Age | Agilité -5→0, gain affiché +5 | 0→0 | Second cas de gain limité à zéro ; pas une preuve du coût de perte sur un échec. |

Le modèle à demi-poids pour les pertes négatives et les poses restant négatives
explique les transitions annotées des quatre caractéristiques primaires.
L'arrivée à zéro doit être traitée distinctement : la Pa Cha observée fournit
une preuve concrète d'un coût de pose entier dans ce cas. Les réussites sans
perte ne consomment pas le puits ; on ne peut donc pas en déduire un coût SN/EC.

Les pertes et le coût de pose sont deux grandeurs différentes. Les correspondances
ci-dessus étayent un modèle comptable pour cette session ; elles ne démontrent
pas l'algorithme de sélection aléatoire des lignes ou les probabilités serveur.

## Analyse du texte « briser le PO, corriger pour 30, repasser le PO »

L'objectif quatre zéros et une Portée est cohérent comme objectif de FM choisi.
Les bornes natives des quatre malus sont -15 : zéro n'est pas leur maximum de
craft fourni par le catalogue.

1. Perdre une Portée retire 51 de densité, mais ne produit pas automatiquement
   51 de nouveau reliquat. Il faut retirer le coût effectif de la pose et tenir
   compte du puits précédent et de toutes les autres pertes.
2. Le demi-poids ne rend pas toutes les corrections gratuites et ne garantit
   pas un maximum de 30 de puits pour tout le parcours. L'arrivée à zéro coûte
   différemment dans la Pa Cha observée ; les échecs consomment sans progresser.
3. La vidéo contredit une protection complète des zéros par le puits : Chance
   retombe de 0 à -3 pendant que 36.5 de puits restent affichés. Une règle de
   priorité des malus améliorés doit être prise en compte.
4. Un repassage de la rune Po (poids 51) en SN peut détériorer les lignes ; un
   reste de puits insuffisant ne suffit pas à les protéger. Un EC ne crée pas
   automatiquement un nouveau puits utilisable : il faut vérifier le bilan.
5. La Portée reste à 1 sur les états relus pendant l'enregistrement. L'ancien
   journal visible dès le début contient des poses antérieures : elles ne sont
   pas des transitions avant/après observées dans cette vidéo. Le brisage puis
   le repassage du PO final ne sont donc pas validés par ce clip.

## Sources documentaires et limites

- [Gamosaurus](https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus)
  signale le coût réduit sur malus et l'exception -1→0 ; source communautaire.
- [Huz](https://huzounet.fr/guides/forgemagie) distingue issues, priorité et
  reliquat. La densité perdue ne constitue pas à elle seule le puits net créé.
- La page DofusDB fournie n'a pas été lisible via l'outil web pendant l'analyse.
  Le catalogue local et les images servent de vérification complémentaire.

Ne pas généraliser le poids négatif de Force/Intelligence/Chance/Agilité aux
autres statistiques sans vérifier leur poids propre. Ne pas déduire un taux de
réussite précis ou une séquence optimale de seize transitions sélectionnées.
