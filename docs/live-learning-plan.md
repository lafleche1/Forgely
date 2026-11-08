# Apprentissage en direct

Objectif : après une tentative attribuée à un objet et une rune confirmés, conserver le contexte avant/après, mettre la mémoire à jour dans le même cycle et rendre son effet visible. Les clics sans résultat lisible ne sont pas des exemples d'apprentissage.

Approche retenue : mémoire locale incrémentale et ajustement prudent du classement existant. Les règles, le budget et les contrôles de lecture gardent la priorité. Les statistiques exactes restent distinctes des comparaisons proches ; aucun taux du jeu n'est inventé. Un modèle opaque nécessiterait des données fiables que nous n'avons pas.

1. Tester puis ajouter `OnlineExperience` : transitions cohérentes, identité/rune isolées, profil complet, voisinage conservateur, influence bornée et faible au premier exemple. Rejouer les données locales au démarrage.
2. Tester puis ajouter `LiveLaboratory.refresh` : lecture des nouvelles lignes SQLite seulement, verrou contre doubles ingestions, mise à jour exacte et mémoire d'expérience atomique. Garder les estimations exactes compatibles.
3. Tester puis raccorder le score d'expérience aux candidats après les contrôles de règles. Expliquer l'ajustement et conserver les probabilités inconnues.
4. Centraliser la sauvegarde des transitions, actualiser la mémoire immédiatement, afficher le nombre et les effets appris dans l'interface et le badge. Réutiliser les contrôles avant/après du pipeline ; ne pas apprendre des prévisualisations.
5. Exécuter les tests ciblés, les parcours natifs isolés et la suite complète. Contrôler notamment les doublons, les comptes/objets différents, les jets incomplets, les données non finies et les objectifs modifiés.

## Vérification réalisée

- Modèle borné à 4 096 exemples récents ; toutes les transitions restent persistées et rejouables au démarrage.
- Les nouvelles lignes sont intégrées sous verrou, sans double comptage entre le thread de fond et l'enregistrement immédiat.
- Le voisinage n'altère pas les taux exacts. Le score est évalué de nouveau pour les objectifs courants et ne double pas l'influence d'une mesure contextuelle exacte déjà utilisable.
- Relecture indépendante : gains positifs sur une autre ligne et autorisation par CSV partiel corrigés, avec tests initialement en échec puis réussis. Les anciens états après incohérents sont également exclus de l'ingestion réelle.
- Les variantes de casse des noms OCR/manuels partagent la mémoire d'expérience ; les identifiants des variantes d'objets restent distincts.
- Suite principale : 517 réussis, 23 ignorés, 42 sous-tests réussis. Parcours natifs isolés ciblés : 11 réussis.
- Mesure synthétique locale, hors capture/OCR : sauvegarde + mémoire 29,23 ms ; comparaison de 4 096 exemples 13,36 ms. Ces chiffres ne prouvent pas un délai complet inférieur à une seconde.
- Limite suivie : un démarrage avec un historique très volumineux ou un verrou SQLite peut retarder la mise à jour synchrone ; sa durée est conservée dans `last_learning.update_ms`.
