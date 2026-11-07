# Forgely 0.20.33 — Lecture avant première rune

La version 0.20.32 exigeait `active_equipment_verified` avant d'accepter une
lecture stabilisée du jet et du reliquat. Or le nom et l'icône de l'objet
n'apparaissent dans l'historique qu'après la première rune, selon le retour
d'utilisation. Cela maintenait l'interface en attente malgré une capture OCR
valide de la table des effets et du reliquat.

## Changements

- `forgely_workshop_readings.py` stabilise le jet et le reliquat après trois
  captures identiques, **sans dépendre de l'identité de l'objet**.
- Le mini-overlay affiche « Attente 1re rune » quand l'atelier est reconnu mais
  qu'aucun nom d'objet n'a encore été trouvé. Si le nom est visible, il indique
  « Objet à confirmer » jusqu'à la confirmation du couple nom/logo.
- La première apparition d'un nom conserve une éventuelle lecture antérieure
  comme baseline **provisoire en mémoire** et invalide la lecture courante : la
  rune peut avoir changé les caractéristiques.
- Une fois le nom et le logo confirmés, la baseline peut être associée à la
  fiche dans l'état de session, mais elle ne génère aucune tentative ni
  transition statistique. Seule une lecture actuelle stabilisée peut être
  utilisée par le copilote.
- Une nouvelle valeur OCR, une tentative, un changement d'objet ou la fermeture
  de l'atelier invalide les lectures courantes potentiellement obsolètes.
- Le diagnostic précise les lectures provisoires et la phase d'identification.

## Limites

- La reconnaissance du nom/logo reste tributaire de la disposition de
  l'atelier et de l'OCR. Les captures de l'utilisateur permettent de vérifier
  la configuration actuelle, pas toutes les échelles et résolutions.
- Aucune attribution rétroactive de tentative à un objet non identifié.
- Tests exécutés sous Linux ; l'intégration Windows doit être validée sur le
  poste utilisateur.
