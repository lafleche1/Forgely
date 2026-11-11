# Conseil pour profils signés, sans simulation automatique

Demande : conseiller les objets avec malus. Maintenir le retrait du simulateur
du parcours en direct, confirmé par l'utilisateur. Le simulateur manuel et
l'entraîneur ne sont pas réactivés ni étendus dans cette étape.

## Choix

Étendre le classement existant aux jet/cibles/bornes signés. Un nombre négatif
n'est pas une lecture invalide. Comparer le progrès nominal vers les cibles et
les paliers connus sans fabriquer de probabilités SC/SN/EC pour ces profils.
Ne pas compter la suppression d'un malus comme du puits déjà gagné. Le poids
nominal reste un indicateur conservateur d'exposition, pas une perte prédite.
Préserver les gardes connues, la complétude et les données réellement illisibles.

L'option de réactiver le modèle archivé Dofocus est écartée : l'utilisateur a
confirmé le retrait des simulations des conseils. Son code est une référence
de recherche, pas une validation des règles serveur.

## Étapes

1. Tests en échec : Tétriste vers zéro, malus au sein d'un objet mixte,
   cibles négatives, passages zéro, tous les profils négatifs du catalogue
   ayant des runes connues. Vérifier taux absents et aucun appel simulateur.
2. Retirer les exclusions générales dans `forgely_decision.py`, classifier la
   remontée négative, préserver les contrôles indépendants et les comparaisons
   de paliers. Ajouter une trace explicite du classement nominal signé.
3. Afficher les limites spécifiques dans l'explication et le rapport matriciel.
   Ne pas restaurer un calcul simulé ou une calibration synthétique.
4. Adapter les tests de l'ancien refus du conseiller ; conserver ceux du refus
   du simulateur signé, qui reste hors périmètre. Vérifier les profils positifs,
   le parcours en direct et l'absence de confusion observations/simulations.
5. Documenter les résultats et les limites dans la note de reprise Work.
