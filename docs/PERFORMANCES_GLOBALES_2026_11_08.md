# Accélération de Forgely — 8 novembre 2026

Mesures reproductibles sur le même environnement Linux/Python, hors capture DOFUS Windows. Données fictives : 2001 noms enregistrés, 10000 lignes de bornes naturelles, 30000 observations de benchmark. Aucun enregistrement fictif n’est inséré dans les données livrées. Les caches sont amorcés avant la mesure.

| Opération | Avant p50 (ms) | Après p50 (ms) | Après p95 (ms) |
|---|---:|---:|---:|
| Nom exact dans les noms enregistrés | 81.340 | 0.063 | 0.089 |
| Bornes naturelles, fichier inchangé | 70.167 | 0.014 | 0.023 |
| Conseil, état identique | 27.203 | 0.135 | 0.221 |
| Conseil, état changé | 26.747 | 4.328 | 5.324 |

La rune sélectionnée dans le scénario de benchmark reste **Fo**. Les chiffres ne mesurent pas la reconnaissance OCR d’un nom à l’écran, l’arrivée d’un résultat DOFUS, ni le délai complet jusqu’à affichage. Le gain varie avec la taille réelle des données et le PC.

## Changements exécutés

- Recherche des noms : index normalisé borné, correspondances exactes par mots et candidats flous par longueur. Les ambiguïtés et doublons restent refusés.
- Lecture du jet et de la rune : motifs précompilés et parsings réutilisés avec résultats immuables. Toute variation de texte produit une nouvelle entrée ; les caches OCR continuent de vérifier les pixels exacts.
- Bornes naturelles : lecture/indexation du CSV une fois par version du fichier, copie fraîche du résultat.
- Statistiques : une requête pour toutes les runes de l’objet, index SQLite couvrant. L’index peut coûter du temps lors de sa première création sur une grande base ; il n’est pas reconstruit à chaque lecture.
- Conseil : une entrée de cache, durée maximale une seconde, jet/cibles/puits/niveau/prix/budget/audit exacts. Révisions base+WAL, laboratoire et références incluses. Le résultat est copié pour éviter les mutations partagées. Une fusion en attente ou un objet non vérifié contourne immédiatement le cache et bloque le conseil.
- Affichage : mêmes textes non reconfigurés, résumé tronqué avant rendu, icône conservée tant que rune/widget/fichier ne changent pas.
- Minuteurs : les saisies manuelles et validations OCR ne créent plus une nouvelle chaîne de rafraîchissements périodiques.
- Laboratoire : les lectures identiques ne reconstruisent plus tous les groupes ; les notifications et une révision publiée conservent l’actualisation des conseils.
- Capture : la durée de capture est déduite de l’attente pour viser une période de120ms plutôt que capture+120ms. Un rendement minimal de5ms est conservé. Aucun seuil de confirmation ou de changement visuel n’est diminué.

## Diagnostic et vérification

Le diagnostic OCR affiche les p50/p95 de calcul des conseils et les compteurs de réutilisation du cache, en complément des mesures existantes de capture et d’identification. Les contrôles de contexte/capture, le suivi du puits, les bilans prospectifs, les objectifs et le budget restent actifs.

Tests : invalidation sur état/prix/laboratoire/WAL/fichier remplacé ; absence d’alias mutable ; ambiguïtés de noms ; icône non recréée ; absence de multiplication des minuteurs ; laboratoire au repos ; période de capture. Suite complète, compilation et revue réalisées. Les tests natifs Windows/Tk nécessitent l’environnement de l’utilisateur.

Reproduire : `python Application/mesurer_vitesse_globale.py --output mesures.json`. Le benchmark crée ses données dans un dossier temporaire, supprimé en fin de mesure.
