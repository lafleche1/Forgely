# Historique visuel Unity et latence

Objectif : reconnaître les groupes de tentatives des captures fournies, sans
confondre les icônes de rune et de caractéristique, puis réutiliser les contrôles
avant/après existants pour l'apprentissage. Ne jamais importer les captures
statiques comme des tentatives de l'utilisateur dans la base de jeu.

- [x] Conserver les captures et leurs annotations comme tests de référence.
- [x] Ajouter un lecteur commun : regroupement par icône de rune, variations
  signées ou positives sans signe, couleurs du texte, variation du reliquat.
- [x] Identifier les runes par références confirmées et gain ; refuser les conflits et
  paliers ambigus. Le résultat doit rester inconnu si des lignes sont illisibles.
- [x] Relier les groupes au suivi des nouveaux événements : référence initiale,
  défilement, répétitions et fenêtres coupées ne doivent pas créer de faux essais.
- [x] Raccorder au lecteur principal, aux états avant/après et au circuit
  existant d'apprentissage, sans ajouter de clics dans le jeu.
- [x] Mettre en cache les groupes inchangés ; mesurer lecture froide/chaude
  sur les vraies captures et vérifier les conseils et calculs existants.
- [x] Exécuter les tests ciblés, puis la suite complète. Documenter les limites
  restantes (échelles, masquage, rune inconnue, malus).
