# Forgely 0.20.37 — OCR de l'icône à gauche du nom

Le premier en-tête de l'historique peut être reconnu sous les formes
`Bar ANNEAU DU CYCLOÏDE D` ou `Ban) ANNEAU DU CYCLOÏDE D` : les glyphes
au début sont produits par le logo de l'équipement. La lecture OCR dédiée,
qui enlève la zone de l'icône, renvoie correctement `ANNEAU DU CYCLOÏDE`.

Auparavant, la comparaison stricte des deux lectures rejetait cet équipement,
remettant l'identification à zéro et laissant l'overlay sur « Objet à identifier ».

Le résolveur accepte désormais un préfixe parasite de 1 à 4 caractères devant
le nom complet, mais n'accepte ni un autre nom d'équipement ni des mots
supplémentaires après le nom. Le logo et le nom doivent toujours être
stables sur plusieurs images avant d'être enregistrés localement.

Testé sur les captures DOFUS fournies (183624, 185548, 190438), ainsi que
sur des cas de conflit volontaire. Test en direct sur Windows encore requis.
