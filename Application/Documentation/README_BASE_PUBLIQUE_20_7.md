# Forgely 0.20.7 — base documentaire publique

Base construite sans intervention de l’utilisateur à partir de guides publics consultés le 6 novembre 2026.

## Livrables
- `reference_sources_fm.csv` : URL, portée et usage de chaque source.
- `reference_poids_fm.csv` : 17 catégories de poids documentaires avec statut de concordance.
- `forgely_reference_publique.py` : lecture prudente de la référence, **sans** l’injecter dans les probabilités ni remplacer les valeurs de production.
- `tests/test_reference_publique.py` : garde-fous anti-probabilités inventées.

## Interprétation
Les tableaux concordants sont essentiellement historiques (DOFUS 2). Ils ne constituent pas une validation officielle des paramètres DOFUS 3. Les valeurs de vitalité et d’initiative exigent particulièrement une vérification du libellé : poids *unitaire* et poids de la *rune* sont souvent confondus. Les données DOFUS Rétro sont exclues du calcul de référence.

Les guides expliquent SC/SN/EC et le reliquat, mais ne contiennent pas d’échantillon brut de tentatives contrôlées. **Taux empiriques ajoutés : 0.** Les statistiques du laboratoire continuent à exiger des observations vérifiées, sans mélange avec la simulation.

## Sources
- https://www.tofus.fr/fiches/forgemagie
- https://www.eclypsia.com/home/dofus/guides/dofus-guide-forgemagie-72756.html
- https://guidedofus.com/v2/guide-forgemagie
- https://github.com/DofMod/SmithMagic
- https://auralithe.online/wiki/forgemagie-et-puits-exos
- https://xixou.io/forgemagie/ (Rétro : comparaison uniquement)

Les références sont informatives et ne remplacent pas les vérifications en jeu.
