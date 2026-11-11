# Analyse du dépôt dofus-fm-server

Consulté le 8 novembre 2026 : https://github.com/Vicfou-dev/dofus-fm-server

Révision master : d434d49244e6b20f7a7525579f62f801026ae17e, commit du 28 juin 2026.

## Vérification effective

- Arbre récursif actuel complet : README.md et dofus-fm.png seulement.
- Une seule branche publiée : master.
- Aucune release GitHub publiée à l’instant de la consultation.
- 23 commits accessibles inspectés, représentant 21 arbres distincts : uniquement README.md, puis README.md et l’image. Aucun ancien code moteur trouvé.
- Le README renvoie vers un site, Discord et des téléchargements externes. Aucun exécutable téléchargé ni lancé.

## Ce que cela permet de conclure

Le produit présenté annonce lecture écran, choix de runes, clics en arrière-plan, sessions multiples et historique de consommation. Ce sont les déclarations de son auteur ; ce dépôt ne permet pas d’en vérifier l’implémentation, la qualité ou les taux de réussite.

Le dépôt public sert de présentation commerciale et ne fournit pas les sources du moteur. Il ne contient ni OCR, ni table de poids exploitable, ni modèle d’apprentissage, ni politique de sélection des runes à comparer à Forgely. Automatiser des clics ne démontre pas que les conseils sont optimaux ou qu’un apprentissage est présent.

Idées pertinentes pour Forgely : objectifs par objet, historique des tentatives, consommation par session et arrêt à l’objectif. Elles doivent être réalisées et mesurées avec les propres observations de Forgely. Rien de ce dépôt n’a été copié dans l’application.

## Références de contrôle

- Arbre : https://api.github.com/repos/Vicfou-dev/dofus-fm-server/git/trees/master?recursive=1
- Branches : https://api.github.com/repos/Vicfou-dev/dofus-fm-server/branches
- Historique : https://github.com/Vicfou-dev/dofus-fm-server/commits/master/
- Releases : https://api.github.com/repos/Vicfou-dev/dofus-fm-server/releases

## Complément : installation fournie par l’utilisateur

Inspection locale en lecture seule de `C:/Users/genef/AppData/Local/Programs/DofusFM`, sans lancer l’exécutable ni importer ses modules. Le contenu installé est distinct du dépôt public et ne peut pas être assimilé à son commit.

Empreinte SHA256 de DofusFM-Server.exe : `64d507c352225e6f9da10cb700136b28dd5b756b50739180ba4ca4aef8245624`.

Le dossier _internal contient 383 fichiers, dont des extensions Python 3.11 compilées avec Cython. Le moteur de décision est présent dans `src/features/smithmagic/logic/core/smithmagic_algo.cp311-win_amd64.pyd`, SHA256 `ecaf16cb641cdad5ebd23ff0e6a4738fe058fff6da89b03d4c0daee9b583859c`. Les noms de fonctions et deux commentaires documentaires sont conservés dans les octets du binaire. Leur lecture révèle l’intention de l’auteur, sans démontrer la totalité du comportement exécuté.

### Choix de runes : ce qui est effectivement documenté

1. **Objectif et plafond distingués.** Le commentaire de `_clamp_rune_index_to_max` indique que dépasser la cible utilisateur peut être envisagé quand du reliquat est disponible. Cela ne signifie pas nécessairement dépasser le maximum naturel : les deux notions doivent rester distinctes.
2. **Taille de rune ajustée à la marge.** Le moteur possède un résolveur de tailles par familles de caractéristiques, puis une vérification supplémentaire de la valeur projetée. Son exemple oppose une ligne Puissance 68/70 à une Ra de +10. Le commentaire précise cependant que dépasser le maximum seul ne déclenche pas toujours la réduction : il considère aussi un plafond de poids de ligne. La valeur exacte de ce plafond et toutes les branches ne sont pas établies par la seule inspection des chaînes.
3. **Puits pris en compte.** `find_best_rune_with_remaining_power` et `_find_stat_rune_for_power` attestent de branches dédiées au reliquat ; les commentaires confirment une vérification de la marge dans cette branche. Ils ne donnent pas le score exact de sélection.
4. **Surplus considéré séparément.** `calculate_overpower_penalty`, `find_best_rune_if_overpower` et `_overpower_ceiling` existent. Le second commentaire indique que, pour un malus naturel dont l’objectif est zéro, atteindre zéro ne doit pas entraîner une compensation automatique sur une autre ligne déjà pleine.
5. **Priorité et objectif complet.** Présence de `get_effect_to_priorize`, `check_goals`, listes d’effets dommages et sans priorité. L’ordre exact, les coefficients, le départage et le moment précis de la tentative d’exo ne sont pas déductibles de ces seuls identifiants.

### Comparaison avec Forgely local

| Idée | État dans Forgely | Utilité / réserve |
|---|---|---|
| Distinguer cible et maximum naturel | Déjà présent dans candidates() et l’environnement : une rune peut dépasser la cible si elle reste dans les bornes naturelles | Préserver ce comportement ; ne pas le présenter comme une nouveauté |
| Choisir simple / Pa / Ra selon marge et poids | Plusieurs tailles déjà comparées, avec progression, dépassement et exposition | Ajouter une explication lisible et comparer plutôt qu’imposer des seuils copiés |
| Intégrer le puits dans le choix | Déjà présent | Vérifier les vrais résultats ; le puits ne rend pas une action gratuite ni garantie |
| Proposer une action préparatoire sur une ligne déjà à cible, y compris over temporaire | Ajoutée au raisonnement partagé et au mode expérimental de l’entraîneur | Options expliquées dans le conseiller ; pas de recommandation automatique sans validation |
| Traiter les malus sans fausse compensation | Le conseiller exclut actuellement les lignes négatives qu’il ne modélise pas suffisamment | Ne pas prétendre qu’elles sont déjà apprises ; nécessite des observations et essais spécifiques |
| Historique par objet et contexte | Déjà présent, étendu aux sessions vidéo | Base utile pour comparer objectivement les stratégies |

### Ce qu’il ne faut pas importer comme vérité

Le commentaire appelle le dépassement de cible avec reliquat un gain gratuit : c’est une appréciation de son auteur, pas une loi de forgemagie. Une rune peut consommer du puits, échouer ou dégrader l’objet. Un over existant n’est pas déjà du puits ; seule la perte effectivement observée entre dans la comptabilité. Le succès critique conserve le puits.

Aucune preuve trouvée d’une politique apprise par entraînement dans les modules inspectés. Les catégories et branches visibles évoquent un moteur à règles, mais ne permettent pas d’exclure une autre logique ailleurs. Aucun modèle local .pt/.onnx/.tflite/.traineddata trouvé. Les formules exactes et les performances réelles restent inconnues.

**Conclusion exploitable :** élargir les stratégies candidates et expliquer leur raison peut être utile ; copier aveuglément les décisions ou considérer ce bot comme un oracle ne serait pas justifié. Les essais sur overs de Forgely restent nécessaires : leur intérêt doit être mesuré sur le jet complet, avec données vidéo fiables, par objet. Aucun composant du bot n’a été intégré ou exécuté.

## Intégration locale réalisée

`forgely_reasoning.py` partage les principes vérifiables entre le conseiller et l’environnement d’entraînement : poids, marge jusqu’à la cible, distinction cible/maximum naturel, couverture théorique du puits et candidats préparatoires limités. Chaque option contient sa raison et son statut expérimental. Les pertes futures ne sont jamais créditées en avance.

Le conseil expose ces raisons et les options à comparer. Le mode virtuel permet l’exploration préparatoire par objet, sans changer le témoin direct ni le critère de jet complet. Les archives classiques restent compatibles ; les états expérimentaux distinguent le surplus exact. Les politiques de ce nouveau domaine ne sont pas promues dans le conseiller sans audit de sélection adapté.

La formule native compilée du bot n’a pas été reproduite ; les seuils exacts de son résolveur, l’ordre complet des priorités et ses performances restent inconnus. Les lignes négatives ne sont pas présentées comme prises en charge si le modèle ne sait pas les valider. Aucun taux de réussite du bot n’a été utilisé comme référence chiffrée.
