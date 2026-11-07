# Forgely 0.20.32 — Identification visuelle locale des équipements

Le nom de l'équipement peut n'apparaître dans l'historique de l'atelier
qu'après la première rune. Forgely ne doit donc pas présumer qu'il connaît
l'objet simplement parce que l'atelier est visible.

## Algorithme

1. OCR du nom sur la première ligne de l'historique.
2. Découpage du logo dans la même ligne (coordonnées relatives au cadrage DOFUS de référence).
3. Rejet des découpes uniformes et contrôle de cohérence du nom/logo sur
   plusieurs images consécutives.
4. Association à la fiche existante par nom normalisé, ou création d'une fiche
   inconnue après double OCR concordant et quatre observations stables.
5. Comparaison des logos locaux pour éviter de réutiliser une identité
   visuelle contradictoire. En cas de conflit, aucun item n'est confirmé.
6. Affichage de l'icône dans la fiche Équipement ; diagnostic et export de la
   découpe pour faciliter la validation terrain.

Le logo est une **preuve supplémentaire**, pas une identité suffisante à lui seul.
Il ne doit jamais autoriser une collecte de statistiques pour un nom incertain.

## Stockage et confidentialité

SQLite local : `equipment_icons` associe un `equipment_id` à un chemin PNG.
Images dans `%LOCALAPPDATA%\\Forgely\\icones_equipements`.
Aucun service distant n'est appelé par cet apprentissage.

## Limites

- Nécessite un nom visible dans la première ligne de l'historique, après la
  première rune dans la configuration décrite par le joueur.
- Le logo peut être mal cadré si la fenêtre d'atelier est déplacée ou si
  l'échelle de l'interface DOFUS est modifiée.
- Les tests unitaires ne valident pas à eux seuls l'intégration Windows en direct.
- Une tentative initiale ne peut pas être attribuée rétroactivement sans
  preuve sûre de son objet et de sa rune.
