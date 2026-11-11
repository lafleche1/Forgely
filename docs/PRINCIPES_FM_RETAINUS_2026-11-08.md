# Principes retenus pour Forgely et son entraîneur

Synthèse du 8 novembre 2026, à partir du guide fourni par le joueur, du
référentiel local versionné et des règles effectivement exécutées. Ce document
ne modifie pas à lui seul les moteurs et ne valide pas les probabilités du jeu.

## Comptabilité à conserver

- Distinguer le poids par point, le gain d'une rune et son poids total.
- Le poids total de la rune est le gain multiplié par le poids par point.
- Un over est un surplus au-dessus du maximum naturel ; un exo est une ligne
  absente d'un profil naturel complet. Une omission OCR ne prouve pas un exo.
- Un surplus présent n'est pas déjà du puits disponible.
- Un SC conserve exactement le puits et ne retire pas de caractéristiques.
- En SN/EC, sur une transition complète et cohérente :
  `puits_après = max(0, puits_avant + poids_des_pertes - poids_de_la_rune)`.
  En SN, une perte sur la ligne visée tient compte du gain nominal de la rune,
  et pas seulement de la variation nette affichée.
- Aucun puits négatif n'est enregistré. Le poids non couvert exige des pertes
  ou signale une lecture/transition insuffisante ; il ne crée pas une dette cachée.
- Seules les pertes mesurées et attribuées à une tentative confirmée peuvent
  certifier un puits calculé. Les situations ambiguës exigent une relecture.

Exemples sans puits initial ni autre perte : perte d'un PA avec une rune de poids
9 = 91 de puits ; perte d'un PO avec une rune de poids 3 = 48 ; perte de trois
points d'Intelligence avec une rune de poids 1 = 2. Si seulement un des trois
points d'over est perdu, ce dernier exemple ne produit aucun nouveau puits.

## Poids du référentiel actuellement livré

| Caractéristique | Poids par point |
|---|---:|
| PA | 100 |
| PM | 90 |
| Portée | 51 |
| Invocation | 30 |
| Résistance élémentaire en % | 6 |
| Dommage élémentaire | 5 |
| Dommage générique | 20 |
| Sagesse | 3 |
| Prospection | 3 |
| Tacle / Fuite | 4 |
| Force / Intelligence / Chance / Agilité | 1 |
| Vitalité | 0,2 |
| Initiative | 0,1 |

Vi apporte 5 Vitalité et pèse 1 ; Pa Vi apporte 15 et pèse 3 ; Ra Vi apporte 50
et pèse 10. Ces valeurs viennent du référentiel client local versionné
`Application/references/poids_runes_client_3_7_13_17.json`, dont la provenance
est explicitée dans `docs/POIDS_RUNES.md`. Il ne s'agit pas d'une table publiée
et certifiée directement par Ankama. Le tableau en image du guide collé n'a
pas été fourni : aucune de ses valeurs n'est déduite d'une image absente.

## Stratégies à maintenir parmi les possibilités

Le joueur demande explicitement de conserver l'over temporaire comme solution
envisageable, même si une première expérimentation n'en démontre pas le gain.
Un résultat synthétique défavorable ne suffit pas à interdire une pratique.

- Remonter en priorité des lignes lourdes ciblées, puis finir les lignes légères.
- Stabiliser des lignes très basses avant une tentative lourde.
- Remettre rapidement une grosse ligne naturelle perdue, puis exploiter le puits
  conservé en cas de SC.
- Exploiter une partie du puits pour préparer le jet avant de remettre cette ligne.
- Utiliser un over déjà présent comme support fragile.
- Créer un over temporaire, éventuellement avec Pa/Ra, puis poursuivre la remontée.
- Envisager un balancier entre lignes, en comptant ce qu'il faut reconstruire.

Ce sont des choix conditionnels à comparer, pas un ordre universel obligatoire.
Leur intérêt dépend de l'objet, du jet initial, des cibles, des runes et du puits.
Les mêmes séquences ne sont pas automatiquement transférées d'un objet à l'autre.
Une ligne non ciblée n'est pas automatiquement exigée au maximum. Les malus
nécessitent des règles distinctes ; les règles positives ne leur sont pas appliquées
silencieusement. Aucun de ces raisonnements n'autorise des clics dans DOFUS.

## Ce qui n'est pas retenu comme règle certaine

- « Un SC vide le puits » : faux dans la règle utilisée ; il le conserve.
- « Un PA perdu donne toujours 100, un PO toujours 51 » : oublie le poids de la rune.
- « Toute baisse d'over donne intégralement son poids en puits » : même omission.
- « Du puits garantit qu'aucune ligne ne peut baisser » : affirmation trop absolue,
  notamment en présence d'overs/exos et lorsque le poids de la rune dépasse le puits.
- « Toujours casser volontairement PA/PM/PO, puis les remettre à la fin » : stratégie
  parmi d'autres, sans garantie de cibler la ligne qui tombera ou d'améliorer le résultat.
- « Attendre exactement 100 ou 51 de puits avant la remise » : seuil non universel,
  qui peut même dépasser le puits créé au départ.
- « Toutes les runes lourdes exotiques ont un taux certain de 1 % » et les seuils
  20/60 présentés comme lois absolues : pas importés comme probabilités officielles.
- Un plafond 100/101 du puits : distinct des garde-fous de densité des over/exos.
- Les anciennes conditions d'accès aux métiers du guide : à ne pas transposer
  automatiquement à la version actuelle du jeu.

## Contrôle de l'objet avant une feuille de route

Le catalogue local et le profil Dofocus de l'Anneau du Cycloïde, identifiant 14092,
ne contiennent pas de Portée naturelle. Une feuille de route basée sur la chute
d'un PO natif n'est donc pas applicable à ce profil. Un PO observé doit être
qualifié à partir de la version et du profil vérifiés, pas supposé naturel.

## Évaluation attendue de l'entraîneur

L'objectif reste le jet demandé complet. Aucun bonus artificiel n'est attribué
à la fabrication de puits. Comptabiliser aussi les tentatives, les dommages sous
les cibles, les abandons et les limites de séquence. Séparer entraînement et audit,
comparer des politiques figées sur les mêmes situations, répéter les entraînements
et conserver les résultats par objet et par configuration.

Les politiques expérimentales restent isolées des politiques chargées par le
copilote. La découverte d'un gain dans le simulateur ne prouve pas un gain en jeu.

## Sources et limites

- Guide fourni par le joueur : texte de « Bonjour chers Douziens ! », sections
  3.1 à 3.8. L'auteur le présente comme issu de son expérience personnelle.
  La section 3.4 reconnaît explicitement deux écoles pour remettre la grosse ligne.
- Lien fourni : https://www.dofus.com/fr/forum/1778-artisanat-elevage/2382087-guide-forgemagie
  (accès direct bloqué par une vérification anti-robot ; analyse du texte collé).
- Référentiel et modules locaux : `forgely_weights.py`, `forgely_decision.py`,
  `forgely_expert.py`, `forgely_rl.py`, `forgely_dofocus_engine.py`.
- Guide communautaire Tofus : https://www.tofus.fr/fiches/forge
- Guide communautaire Alterya : https://alterya.over-blog.com/article-la-forgemagie-103398969.html

Un texte hébergé sur le forum Ankama reste une contribution communautaire ;
ses hypothèses ne deviennent pas automatiquement une spécification officielle.
