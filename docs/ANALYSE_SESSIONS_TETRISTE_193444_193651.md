# Complément vidéo Tétriste — 10 novembre 2026

Analyse locale des enregistrements 193444 (129,1 s) et 193651 (30,53 s).
Échantillonnage toutes les 0,5 s, puis comparaison visuelle des images des
transitions retenues. Les lectures manquantes ne sont jamais remplacées par zéro.
Les deux clips se raccordent : fin 193444 et début 193651 avec PO 0,
Force/Intelligence/Chance -15, Agilité -1, reliquat 24,5.

## Deuxième clip, 193444

Le PO demeure à zéro dans les états lisibles. Attention : « 0 Portée » ne doit
pas être confondu avec « 1 Portée » dans les miniatures. Le reliquat évolue de
41 à 24,5. À 68 s, Agilité passe de -11 à -1 et le reliquat de 31,5 à 26,5 :
coût observé de 5 pour une Ra Age de gain 10 restant entièrement négatif.
Les pertes sur les autres malus améliorés apparaissent avant épuisement du puits.

## Troisième clip, 193651 : observations vérifiées sur images

| Temps | Transition | Reliquat | Observation |
|---|---|---|---|
| 0–1,5 s | PO 0 → 1, autres lignes inchangées | 24,5 → 24,5 | Une tentative PO échouée précède la réussite. Deux poses, pas une transition unique. |
| 6–6,5 s | Intelligence -4 → +6 ; Agilité -12 → -15 | 24,5 → 16 | Ra Ine : charge totale compatible avec 10, dont 1,5 de perte sur malus et 8,5 de reliquat. |
| 12,5–13,5 s | PO 1 → 0 ; Chance reste -5, autres stats -15 | 2 → 43 | Ra Cha échouée, stock 31 → 30 : bilan 2 + 51 - 10 = 43. |
| 20–20,5 s | PO 0 → 1, quatre malus à -15 | 33 → 33 | Repassage sans perte visible. |
| 23,5–24 s | Intelligence -4 → +6 ; autres lignes inchangées | 33 → 23 | Ra Ine, stock 186 → 185 : charge directement observée de 10. |

## Conséquences pour les règles

- Une ligne nativement négative peut dépasser zéro. Les gains +5 observés
  précédemment depuis -5 ne prouvaient donc pas un plafonnement universel à zéro.
- Le franchissement -4 → +6 coûte ici la densité entière de la rune Ra Ine (10),
  et non 5, ni un calcul proportionnel 4 × 0,5 + 6 × 1 = 8.
- La même Ra peut coûter 5 lorsqu'elle reste négative et 10 dans une tentative
  où elle n'aurait plus une destination négative. L'échec Ra Cha à Chance -5,
  avec chute du PO, fournit un second bilan cohérent avec une charge de 10.
- La chute du PO ne donne pas automatiquement 51 de puits net : ici +41.
- Les repassages observés conservent le puits. Ils ne renseignent pas sur les
  pertes d'un repassage en succès neutre ; ne pas extrapoler à ce cas.

Ces observations portent sur cette amulette et les quatre statistiques de base.
Elles ne suffisent pas à établir les probabilités, tous les cas limites à zéro,
ni la sélection exhaustive des pertes pour tous les profils avec malus.

## Traçabilité et absence de modification du moteur

Images de preuve : `work/session_malus_20261110_193651/proof_*.png`.
Lectures : `timeline.json`, `changes.json` dans chaque dossier de session.
`reviewed_evidence.json` conserve l'empreinte SHA-256 du troisième fichier et
les états retenus. Les OCR peuvent omettre une ligne visible sous infobulle :
la revue visuelle prévaut, sans compléter automatiquement ces JSON.
Aucune importation de données inférées dans la base, aucune simulation réactivée,
aucune modification des règles exécutées par le moteur dans cette analyse initiale.

## Intégration demandée ensuite

Le suivi de puits et l'audit utilisent désormais un calcul partagé pour les
transitions complètes : demi-charge des quatre statistiques de base si la
destination nominale reste négative, charge entière à zéro ou au-delà, et
pertes des mêmes statistiques pondérées séparément en positif et en négatif.
Les autres poids négatifs et les gains partiels sur la ligne ciblée restent
inconnus. Un SC ne conserve le puits calculé que si le gain nominal est cohérent.
Le conseil expose la charge applicable, sans prédire les pertes ni réactiver
de simulateur. Les lectures directes restent prioritaires et un puits initial
inconnu ne se reconstruit pas à partir d'une chute du PO.

Validation : 136 tests passent, dont les transitions vidéo, le rejet des
contradictions, les doublons, les profils signés et les gardes OCR ; compilation
des trois modules modifiés réussie. Aucune vérification de la session DOFUS
en cours ni remplacement d'un exécutable distribué n'a été effectué.
