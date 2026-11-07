# Forgely 0.19.9 — Recherche documentée et raisonnement prudent

Cette version ajoute `forgely_connaissances.py` : faits classés par provenance, règles FM / brisage séparées, conflits documentaires, et alertes de contexte intégrées à l'explication des conseils (`forgely_decision.py`).

## Principes de décision
- Aucune probabilité SC/SN/EC fabriquée à partir des guides.
- Un puits non confirmé bloque déjà les recommandations ; ne jamais le remplacer par l'écart au jet parfait.
- Un équipement sans bornes naturelles connues ne doit pas être classé exo/over avec certitude.
- Une rune lourde déclenche une mise en garde contextualisée, pas un pourcentage inventé.
- Observations réelles, résultats de simulation et règles communautaires restent séparés.
- Les règles de brisage (focus, coefficient) ne pilotent pas les taux de pose de runes.

## Sources consultées (novembre 2026)
- https://www.dofuspourlesnoobs.com/guide-forgemagie.html
- https://dofusfashionista.gg/fr/forgemagie/
- https://dofus.jeuxonline.info/article/3736/forgemagie (guide ancien : historique)
- https://www.wiki-dofus.eu/w/Forgemagie (guide communautaire : vérifier version)
- https://dofus-portals.fr/forgemagie/
- https://www.dofocus.fr/guide/ (brisage et focus, pas taux de FM)
- https://www.dofocus.fr/about/ (provenance DofusDB, prix communautaires)
- https://beta.dofusdb.fr/en/database/objects (catalogue, version à vérifier)

## Divergences non résolues
Certains tableaux ne concordent pas sur des poids de runes, et des pages mélangent estimation de poids manquant et reliquat effectif. Un wiki de serveur alternatif n'est pas une preuve des règles du jeu officiel. Les valeurs du catalogue existant ne sont **pas** écrasées sur ces seules sources.

## Limites
Aucune nouvelle vidéo analysée, aucune capture Windows réelle vérifiée, aucune formule secrète reconstituée. Le module est un socle de connaissance et des garde-fous, pas un modèle statistique entraîné.
