# Classement des réparations et tentatives observées — 8 novembre 2026

## Constats reproduits

La capture de 21 h 55 présente l'Anneau du Cycloïde avec Vitalité 294, Force 38,
Intelligence 36, Agilité 37, Dommages Neutre 3, Terre 0, Feu 11, Air 6,
Initiative 276, Résistance Eau 0, Tacle 1 et un puits de 0,1. En jet parfait,
le classement final proposait Vi : le filtre de faible réserve éliminait les
réparations lourdes, puis favorisait la réussite de la prochaine rune plutôt
que la remontée des lignes déficitaires. Le progrès relatif par ligne favorisait
aussi une petite finition presque terminée.

La capture de 21 h 56 montre une observation arrêtée avec une ancienne rune
encore affichée. Les valeurs « À revérifier » ne devaient pas autoriser cette
recommandation active.

L'historique visible contient des variations et du reliquat, mais pas de texte
SC/SN/EC. L'ancien détecteur annulait sa référence dans ce cas. Son autre suivi
de variations comptait des lignes, pas des tentatives, et ignorait les lignes
de reliquat seul : il ne pouvait pas servir de compteur de tentatives.

## Corrections

### Conseil

Les réparations naturelles de poids différents sont comparées selon le poids
réel restauré vers la cible et le déficit pondéré. Le filtre de faible puits
ne remplace plus cet ordre par une préférence systématique pour les petites
runes. Les contraintes légales, les maximums naturels, la priorité aux lignes
naturelles avant les over/exos et les séquences validées restent conservés.

Sur le cas fourni, le résultat devient **Pa Do Terre**, à la place de Vi.
Les tests couvrent plusieurs niveaux de réserve, l'Alliance Boletée, les caps
naturels et le retour aux petites finitions lorsque les grosses lignes sont
restaurées. Le choix reste heuristique : aucune meilleure probabilité officielle
ni réduction garantie du nombre de runes n'est annoncée. Une rune lourde avec
peu de réserve reste exposée à des pertes, qui continuent à être affichées.

Une observation arrêtée, masquée, ou un jet non stabilisé suspend désormais
la recommandation active et enlève l'icône de rune. L'objet, les objectifs et
les anciennes valeurs peuvent rester affichés comme données à revérifier,
sans présenter l'ancien conseil comme actuel.

### Tentatives sans résultat explicite

Un nouveau détecteur utilise l'icône de rune dans la marge gauche pour délimiter
les groupes. Les lignes de caractéristiques et de reliquat qui suivent restent
des continuations du même groupe. La fixture issue de la capture possède
**deux groupes**, et non trois tentatives correspondant aux trois lignes de texte.

Le comptage nécessite une référence initiale stable, puis deux captures fraîches
identiques d'une insertion de nouveaux groupes avec conservation des anciens
groupes et du même en-tête. Les images et le contexte du logo délimitent la
session ; une identification de nom temporairement absente ne réinitialise pas
à elle seule cette référence.

Les anciennes lignes présentes à l'ouverture sont affichées comme référence
initiale, jamais enregistrées rétroactivement comme nouvelles actions. Une
capture coupée en bas, un défilement apparent ou une association ambiguë ne
produisent pas de tentative ajoutée. Les groupes identiques répétés ne sont
comptés que lorsque les deux fenêtres sont complètes, avec une grande marge
vide et sans contenu de barre de défilement dans la gouttière droite.

Les événements acceptés possèdent un identifiant unique et un contexte immuable.
Une livraison répétée ne crée pas une seconde observation. Ils sont conservés
dans une table distincte `observed_attempt_activity`, avec résultat indéterminé.
Ils ne sont jamais transformés en SC/SN/EC, ni mélangés aux dénominateurs des
taux ou aux transitions d'apprentissage.

Le fil de lecture signale ces tentatives. L'historique et le compteur local
les montrent avec la mention « résultat à déterminer ». La carte de statistiques
est explicitement globale, tous objets : les tentatives sans objet attribué
ne sont pas ajoutées au total de chaque équipement sélectionné. Les probabilités
contextuelles des runes restent filtrées par équipement.

## Limites explicites

- La famille d'icônes grises de rune visible dans cette capture est prise en
  charge. La couverture de toutes les autres icônes n'est pas démontrée.
- Le détecteur s'abstient sur les fenêtres partielles et le défilement. Il ne
  garantit pas le comptage intégral d'une longue session avec historique tronqué.
- Les tentatives manquées avant ce correctif ne peuvent pas être reconstituées
  de façon fiable à partir des seules captures fournies.
- Le comptage d'une tentative n'est pas sa classification. Les résultats
  sans texte explicite restent indéterminés dans cette livraison. Pour déduire
  SC/SN/EC, un futur classificateur devra notamment distinguer consommation de
  puits et perte de ligne et s'assurer qu'aucun gain n'a échappé à la lecture.
  Un SN ou un EC peut consommer seulement du puits : l'absence de ligne rouge
  ne suffit pas à conclure SC.

## Vérification

Les défauts de classement, de conseil périmé et de persistance séparée ont
été reproduits par des tests échouant avant correction. Les tests de groupes
utilisent une fixture réelle pour les deux ancrages et des insertions synthétiques
pour la chronologie : ce n'est pas une validation vidéo d'une session entière.

La revue a trouvé un mélange de portée : les événements sans attribution
étaient ajoutés aux chiffres de l'objet sélectionné. Un test a reproduit ce
cas ; la carte a été rendue explicitement globale.

Tests ciblés : classement et caps, suspension après arrêt/masquage, initialisation,
reliquat seul, continuations, répétitions, découpage/défilement, livraison double,
persistance, statistiques SC/SN/EC inchangées. Le journal complet final est
`.test-tmp/attempts-advice-pytest-final.log`.

Résultats : un passage global a terminé avec **1 818 tests réussis, 30 ignorés
et 42 sous-tests réussis**, sans échec. Après le dernier ajustement de la clé
de suivi (icône actuelle, sans les boutons voisins), le groupe ciblé de **35
tests** a passé également, y compris le parcours de l'observateur. Les chiffres
et la détection des deux ancrages de la capture sont dans
`docs/conseil-tentatives-validation-2026-11-08.json`.

Les règles communiquées ensuite par l'utilisateur sont utiles pour un futur
classificateur. Elles nécessitent deux précisions : SN et EC peuvent consommer
uniquement du puits, et l'absence de gain dans un OCR incomplet n'est pas une
preuve d'échec. La classification automatique du format sans libellé n'est
pas activée dans cette livraison.

Références consultées : [Gamosaurus](https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus),
[Tofus](https://www.tofus.fr/fiches/forgemagie). Le fil du forum DOFUS fourni
est protégé par une vérification JavaScript et n'a pas pu être lu.

Cette livraison ne simule aucune action dans DOFUS et ne reconstruit aucun taux
de succès. Les actions non classées sont exclues de l'apprentissage.

## Application

Fermer puis relancer `OUVRIR FORGELY.bat`, démarrer l'observation et laisser
établir la référence initiale avant de vérifier le compteur sur de nouvelles
tentatives. Aucun binaire ni modification distante n'a été publié ; le dossier
local reste sans métadonnées Git.
