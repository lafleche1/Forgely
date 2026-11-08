# Répartition des pertes SN/EC — recherche du 8 novembre 2026

## Résultat

La recherche a retrouvé des descriptions de priorité et des observations, pas une loi publique exhaustive permettant de calculer P(ligne perdue | état, rune, résultat). Aucun coefficient universel de sélection n'est donc certifié dans Forgely.

### Sources directement consultées

- [Huzounet, guide signé et mis à jour le 30 septembre 2026](https://huzounet.fr/guides/forgemagie), section « Règles annexes », indique que les stats en over/exo sont prioritaires lors des poses suivantes. La section reliquat explique l'équilibrage des densités. C'est un guide communautaire d'auteur, pas une spécification Ankama du tirage.
- Vidéo fournie par l'utilisateur « J'ai cracké le secret de la forgemagie DOFUS », vers 2:28–2:55 : son auteur annonce 0,5 % de chute du PA naturel sur SN/EC avec une rune de poids 1, contre 4 % avec une rune de poids 20. Il décrit des fréquences observées ; il ne donne ni effectifs conditionnels par sous-groupe ni fonction générale de tirage des lignes. Les deux points ne suffisent pas à déterminer cette fonction.
- [DoFocus, simulateur de l'auteur](https://www.dofocus.fr/forgemagie/) : l'écran public récupérable ne contient pas une spécification détaillée de distribution des pertes.
- L'accès direct tenté à un ancien billet du devblog Ankama n'a pas permis de lire une source officielle exploitable. Ne pas transformer cette absence de résultat en preuve qu'aucune publication n'existe.

Les résultats portant sur Wax, Sunrise, Aléa ou d'autres serveurs alternatifs ont été exclus : leurs taux et règles spécifiques ne définissent pas DOFUS officiel. Les guides historiques peuvent signaler des priorités, mais leurs anciens poids et leurs exceptions ne sont pas importés automatiquement dans le modèle DOFUS 3.

## Conséquences exécutables

1. Le tirage SN/EC reste distinct du choix des pertes. Une formule SC/SN/EC seule ne définit pas la transition complète du jet.
2. Une perte réelle qualifiée du même objet, jet, puits, rune ET résultat peut être rééchantillonnée : on reproduit le vecteur complet des pertes plutôt que de tirer chaque ligne indépendamment. La banque est lue en lecture seule et les nouvelles trajectoires restent synthétiques.
3. Sans échantillon correspondant, un over/exo existant interdit d'affirmer « puits suffisant donc aucune ligne ne bouge ». Le mode prudent interrompt cette transition et la compte comme inconnue.
4. Le mode approximatif offre un scénario explicite : priorité aux lignes over/exo autres que la ligne visée avant le puits, tirage uniforme au sein des groupes, puis autres lignes. Les quantités retirées et les probabilités de sélection sont des hypothèses ; ce n'est pas l'algorithme retrouvé du serveur.
5. Pas de loi 1/poids, pas d'interpolation des deux taux PA et pas de taux identique imposé à tous les objets. Les bornes de réussite virtuelle signalent les trajectoires non résolues.

Pour identifier plus précisément la loi, il faut des transitions avant/après complètes avec toutes les lignes candidates et leurs bornes, le reliquat avant, la rune et le résultat. Une validation sur des sessions réelles séparées est nécessaire avant de généraliser à d'autres jets. Multiplier les simulations d'une règle supposée ne valide pas cette règle.
