# Prix des runes Tylezia — 8 novembre 2026

À la demande du joueur, le copilote utilise à nouveau les prix des runes.
Le catalogue local est `Application/assets/prices/tylezia-20261108.csv`.
Les valeurs sont les **prix moyens unitaires affichés**, en kamas ; la colonne
« Niveau » des captures n'est pas une quantité et ne sert pas de diviseur.

Les 105 prix ont été récupérés dans la mise à jour GitHub envoyée depuis le téléphone (commit 018157e). Le JSON `Application/prices/tylezia-2026-11-08.json` et le CSV contiennent les mêmes montants.

## Calcul dans le copilote

- Le prix unitaire est affiché dans le conseil principal, son détail et le résumé flottant.
- Le mode **Budget optimisé**, activé lors de l’installation de cette référence, pondère les scores positifs de progression par `1 + prix unitaire`. Il favorise les choix économiques sans promettre le coût minimal du jet complet. Le mode **Chances maximales** reste sélectionnable dans les paramètres. Si des prix candidats manquent, la pondération économique est ignorée.
- Le prix départage les choix à égalité de priorité. Il ne remplace pas la légalité,
  les cibles, la priorité de phase ni un choix de séquence déjà validé.
- Le coût indicatif de remontée d'une ligne vaut le nombre nominal de poses,
  multiplié par le prix unitaire, puis divisé par la probabilité SC+SN du modèle
  courant lorsqu'elle est disponible. Cette approximation conserve le taux actuel
  et **ignore les pertes collatérales et réparations**. Ce n'est pas le coût garanti
  du jet complet, ni une prédiction officielle du jeu.
- Un prix manquant reste inconnu ; il ne donne pas un avantage artificiel de gratuité.
  Si un groupe à égalité comporte un prix inconnu, le classement antérieur est conservé.
- Aucun budget dur n'interdit une rune ciblée. L'entraînement conserve son objectif
  de jet complet et les résultats d'audits précédents restent des résultats sans
  objectif monétaire. Ils ne prouvent pas une amélioration de ce nouveau classement.
- Les prix sont datés et spécifiques à Tylezia. Le fichier est relu après modification.
  Aucune collecte automatique de prix en direct ni fusion avec les observations SC/SN/EC.

La publication GitHub et la copie locale utilisent le même CSV. Les politiques
expérimentales restent inactives sans les validations requises ; la version de
validation du sélecteur est changée pour distinguer le classement avec prix.
