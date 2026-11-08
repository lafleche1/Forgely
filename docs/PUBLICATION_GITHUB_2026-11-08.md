# Publication complète — Forgely v22.15, 8 novembre 2026

Cette publication rassemble la copie locale du copilote, le simulateur,
l'entraîneur, les tests et leurs résultats. Les prix Tylezia sont réintégrés au
copilote à la demande du joueur : 105 relevés unitaires récupérés depuis la mise à jour du téléphone sont fournis. Voir
[les données, calculs et limites](PRIX_RUNES_TYLEZIA.md).

L'apprentissage généralisable reste expérimental et décoché par défaut : l'audit
indépendant a obtenu 834/1000 jets complets contre 860/1000 au témoin et 840/1000
pour l'ancienne politique. Aucun gain dans DOFUS n'est revendiqué.

## Récupérer toute la version

Télécharger le dépôt au format ZIP et le décompresser. Double-cliquer sur
`OUVRIR_VERSION_COMPLETE.bat` : les morceaux de l'archive sont réunis, leurs
empreintes sont vérifiées et **un nouveau dossier** contenant toute la version
est créé. L'exécutable `Entrainement_Forgely.exe`, les icônes, les sources et les
historiques simulés y figurent. Aucun dossier de travail existant n'est remplacé.
Le copilote source utilise son lanceur habituel et ses dépendances Python ;
l'entraîneur compilé est autonome. Voir [la restauration](../distribution/README.md).

Les sources, les prix et les rapports sont également consultables directement
dans le dépôt. Les environnements Python, les fichiers temporaires et les bases
personnelles d'observations sont exclus. Les icônes téléchargées et les archives
de simulations sont fournies dans la version complète plutôt qu'en milliers
de fichiers additionnels à la racine du dépôt.

## Reproduire les audits

L'archive `artifacts/training-policies-20261108.zip` contient les deux politiques
figées et leurs métriques, avec leurs chemins d'origine. L'extraire à la racine
d'une copie du dépôt permet d'exécuter les commandes des rapports. Ces archives
ne sont pas automatiquement activées par le copilote.

- [Rapport de correction](RAPPORT_ENTRAINEMENT_2026-11-08.md)
- [Rapport de généralisation et audit final](RAPPORT_GENERALISATION_2026-11-08.md)
- [Résultats structurés](general-policy-final-audit-2026-11-08.json)

Vérification finale après fusion du téléphone : **1 543 tests réussis,
25 ignorés, 42 sous-tests réussis**. La suite complète passe dans cet environnement,
avec Tesseract disponible. L'exécutable autonome reconstruit avec les poids partagés
réussit son autotest. Cela ne démontre aucun gain de performance en jeu.

Les résultats 834/1000, 840/1000 et 860/1000 sont les audits historiques avant la
fusion des nouvelles règles et du référentiel de poids. Ils ne constituent pas
une validation du nouveau classement économique. Les graines, rapports et
politiques sont conservés sans modification.

Les commits du téléphone 018157e et 1c65280 sont intégrés à la copie locale :
105 prix, poids communs aux moteurs, tableau conditionnel SC/SN/EC et audit des
transitions confirmées. Le classement économique est une heuristique ; les coûts
indicatifs ne couvrent pas toutes les réparations. Les anciennes préférences du
PC sont sauvegardées et la référence Tylezia est activée en mode Budget optimisé.
