# Forgely 0.20.1 — Sources et probabilités

Le fichier `forgely_recherche_probabilites.py` contient un registre de sources avec **version, nature, portée et usage autorisé**. Les tableaux Rétro, les taux de serveurs privés et les témoignages ne sont **pas** injectés dans les taux DOFUS 3.

## Ce que le module calcule

- Pour un taux **supposé** constant `p` et `n` essais indépendants : `P(au moins un succès) = 1-(1-p)^n`.
- Nombre d'essais pour atteindre une probabilité cible sous ces hypothèses.
- Coût moyen des runes : `prix_rune / p` (sans réparations, non représentatif du coût total d'une FM).
- Un scénario **illustratif** à 1 % pour certains exos lourds, étiqueté non calibré pour DOFUS 3.

Ces calculs mathématiques sont exacts **conditionnellement aux hypothèses**, mais ne prouvent pas que les essais dans le jeu sont indépendants ni que p reste constant.

## À ne pas faire

- Ne jamais utiliser les chiffres DOFUS Rétro 1.27 ou ceux d'un serveur privé comme taux DOFUS 3.
- Ne jamais mélanger les tentatives simulées, non vérifiées, les SC/SN/EC et un éventuel EN sans audit de nomenclature.
- Ne jamais annoncer un taux par rune sans jet, puits, poids et échantillon validé.

## Suite du travail

Exporter des tentatives réelles vérifiées, relever l'issue et les pertes par ligne, vérifier si EN apparaît réellement dans l'historique DOFUS 3, puis entraîner et **évaluer hors échantillon** deux modèles distincts (issue, pertes). Pas de changement automatique du conseiller avant validation.
