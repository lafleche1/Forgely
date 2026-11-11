# Fusion ciblée PC et GitHub — 8 novembre 2026

## Intention et approche choisie

Conserver les fonctions locales de vision, sélection d'équipement, jet cible,
conseils et apprentissage ; intégrer les améliorations compatibles du dépôt privé.
L'utilisateur a choisi la fusion ciblée plutôt que la simple publication de la
copie locale sur une branche séparée. Une substitution des fichiers locaux par
ceux de GitHub est exclue.

## État vérifié

- Copie locale sans métadonnées Git, version déclarée 22.15.
- GitHub main : f3d94809126a6d452c028e8ac72d63b312dca3e4.
- Suite locale avant fusion : 1543 réussites, 25 exclusions, 42 sous-tests réussis.
- Tesseract disponible dans C:/Program Files/Tesseract-OCR ; les tests utilisent
  un dossier temporaire dans le projet.
- Le chat référencé ne contient aucun détail technique au-delà d'une demande
  d'envoi au projet. Les documents et le code sont donc les références disponibles.

## Conception proposée

1. Sauvegarder les fichiers concernés avant toute modification. Préparer une
   copie de travail distincte, fondée sur le dépôt distant actuel.
2. Y fusionner les ajouts locaux sans retirer les fonctions distantes. Comparer
   les conflits et préserver les garde-fous de confirmation des lectures.
3. Intégrer la recherche indexée des noms, les expressions précompilées et caches
   bornés d'analyse OCR, les lectures groupées de statistiques et les mises à jour
   d'interface évitant le travail répétitif. Adapter la cadence de capture.
4. Ne porter le cache de conseils que si toutes les dépendances locales peuvent
   être invalidées : jet, cibles, puits, identité/session, prix, profils, base/WAL,
   apprentissage et simulation. À défaut, conserver le calcul local sans cache.
5. Garder l'apprentissage expérimental désactivé sans validation indépendante.
   Aucun taux de réussite ni gain en jeu ne sera déduit de tests synthétiques.
6. Exécuter les tests locaux et distants pertinents, la suite complète et la
   compilation. Documenter les exclusions et limites avant publication.
7. Publier les sources fusionnées validées sur une branche dédiée du dépôt privé
   et ouvrir une proposition de fusion. Conserver main et l'archive de distribution
   actuelle tant qu'une nouvelle distribution n'a pas été reconstruite et testée.
8. Contrôler à nouveau le commit distant avant publication ; intégrer tout nouveau
   changement avant de publier, sans forcer une référence Git.
9. Reporter les sources fusionnées validées dans le dossier local après sauvegarde
   et contrôle des empreintes de départ. Si un fichier local a changé entre-temps,
   le comparer à nouveau plutôt que le remplacer.

Périmètre validé par l'utilisateur dans ce chat. Le résultat attendu est une
version locale réunissant les travaux PC et GitHub, puis sa publication validée.

## Limites et choix laissés à l'implémentation

La fusion ne crée aucune automatisation de saisie dans DOFUS. Les observations
personnelles, secrets, captures privées et environnements Python ne sont pas
publiés. Les ressources nécessaires sont reprises seulement après contrôle de
leur provenance. Le seuil de moins d'une seconde exige une mesure en jeu et ne
fait pas partie des résultats déjà établis. La sélection des optimisations
compatibles et la résolution des conflits relèvent de l'implémentation.
