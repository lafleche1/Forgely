# Matrice prédictive de Forgely 22.14

La matrice demandée est active en observation automatique et en sélection
manuelle. Elle classe les runes compatibles avec le jet souhaité et les gardes
existantes ; elle ne réalise aucun clic dans DOFUS.

| Puits observé ou calculé | Politique |
|---|---|
| Au moins 51 | Lignes lourdes naturelles à remonter, dont le poids est couvert ; petites runes écartées. |
| De 20 à moins de 51 | Lignes intermédiaires prioritaires ; comparaison du gain nominal par unité de poids. |
| Strictement positif et inférieur à 20 | Grignotage des statistiques de base et de la vitalité, avec de petites runes. Les valeurs fractionnaires sont prises en charge. |
| Zéro | Si saturation indicative inférieure à 75 %, nettoyage par une Ra admissible lorsqu’il en existe une ; sinon stabilisation à risque. Aucune perte ni création de puits n’est certaine. |

## Estimations de réussite

Les fourchettes fournies par l’utilisateur sont enregistrées comme hypothèses
théoriques : 60–70 % sous saturation, 30–45 % près du maximum (seuil indicatif
de saturation pondérée : 90 %), 20–30 % pour un over inférieur à 20 %, 10–15 %
pour les autres overs/exos secondaires, 1 % pour un exo majeur PA/PM/PO.
Elles ne deviennent pas des statistiques de parties réelles et ne modifient
pas les observations ni le mélange des preuves existantes. Un profil incomplet
ne permet pas de calculer la saturation globale ni de conclure à l’absence
naturelle d’une ligne. Les prix des runes restent exclus du calcul.

## Puits caché

Le registre utilise Decimal. Un SC conserve le puits. Un SN/EC est comptabilisé
à partir du puits précédent, du poids perdu effectivement observé et du poids
de la rune. Le poids perdu sur la caractéristique montée inclut l’éventuelle
perte masquée par le gain de cette même rune.

Un puits devenu illisible peut être calculé seulement depuis une valeur connue
et stabilisée, avec les jets complets avant/après, une seule nouvelle tentative
identifiée et un résultat connu. Un changement d’objet/compte/génération de
capture, une observation incomplète ou une ambiguïté interrompt cette continuité.
Un puits initialement inconnu ne devient jamais zéro par défaut. Une lecture
directe actuelle prend la priorité sur une estimation calculée.

## Affichage

Le détail des conseils présente **[ÉTAT MATRICIEL]**, **[PRÉDICTION DU TOUR]** et
**[RECOMMANDATION IA]**. Les jets sont comparés aux maximums connus ; le puits
est indiqué comme lu, calculé ou inconnu. L’option optimale et une alternative
compatible affichent la fourchette théorique et l’effet conditionnel sur le
puits : SC inchangé, SN/EC avec ou sans pertes observées.

Le panneau flottant en présente une synthèse compacte. Une suspension de lecture
efface les scénarios devenus périmés. Si aucune rune ne satisfait la phase de
la matrice et les contraintes, Forgely explique le blocage au lieu d’en inventer une.

Références de poids conservées : https://dofocus.fr/forgemagie/ et
https://dofocus.fr/guide/. Les pourcentages de la matrice proviennent de la
consigne utilisateur, et ne sont pas attribués à ces références.

## Validation

Suite complète : 1 470 tests réussis, 24 ignorés, 42 sous-tests réussis.
Les derniers garde-fous de continuité et le format exo SC uniquement ont aussi
été vérifiés par les tests ciblés (39 réussis, puis 18 sur les modules modifiés).
Une transition sans résultat identifiable arrête l’attente après six observations
stables et laisse le puits caché inconnu.
