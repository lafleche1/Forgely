# Identification rapide des équipements

Demande : icône + catégorie + bornes naturelles, OCR du nom au départage,
cache, audit reproductible et mesures sans extrapolation.

Architecture retenue : index local immutable des équipements et des images
officielles, pHash DCT 64 bits pour présélection puis distance RGB. La catégorie
est un filtre dur lorsqu'une observation indépendante la fournit. Ne jamais la
déduire du nom supposé. Trois bornes naturelles concordantes, aucune contradiction
et une marge visuelle sont nécessaires pour éviter l'OCR. Les noms homonymes ne
peuvent être activés automatiquement. Les confirmations temporelles restent actives.

Alternatives : OCR systématique (coût actuel) ; icône seule (collisions possibles).
La combinaison demandée est retenue. Aucun nouveau modèle ni service distant.

1. Tests RED : collisions, catégorie, signatures partielles/contradictoires,
   OCR restreint, abstention, invalidation du cache, branche du lecteur réel.
2. Index et résolution dans Application/forgely_equipment_identity.py ; intégration
   dans forgely_item_identity.py et forgely_continuous_identity.py.
3. Audit SHA-256 fichiers/pixels et pHash : fichiers réellement présents, manquants,
   groupes exacts et paires proches sans assimilation à une identité commune.
4. Benchmark séparant construction froide, recherches chaudes, cache et OCR simulé.
5. Suite de régression, rapport avec limites terrain, fichiers de résultats.

Vérifier particulièrement : icônes identiques entre catégories, une seule borne
incompatible, icône vide, OCR hors candidats, changement d'effets malgré nom stable.
Le dossier local n'est pas un checkout Git. Ne pas publier de modifications distantes
sur la seule base de l'accès technique. Livrer les sources et leur empreinte.
