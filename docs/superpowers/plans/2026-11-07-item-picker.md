# Item picker implementation plan

Goal: catégorie → objet → jet souhaité → session, sans attente OCR du nom.
Architecture: catalogue local pur, sélecteur Tk indépendant, association manuelle à l'icône courante de session. Réutilisation des objectifs existants.
Spec: docs/superpowers/specs/2026-11-07-item-picker.md

- [x] Catalogue : tests puis chargement des noms, types et icônes réelles ; recherche accent-insensible ; exclusion des types hors équipement.
- [x] Interface : grille paginée, catégories, recherche, sélection puis formulaire de cibles avec bornes disponibles et caractéristiques supplémentaires.
- [x] Session : sélection explicite requise, cibles associées au bon objet, OCR nom évité en mode manuel ; invalidation au changement d'objet ou de compte ; pas d'enregistrement de référence visuelle manuelle dans le catalogue automatique.
- [x] Vérification : tests du catalogue, validation des cibles, association/invalidation de session, contrôle visuel Tk et régressions disponibles.

Review focus: icônes partagées ; cibles d'un ancien objet ; changement de compte ; annulation du formulaire ; catalogue ou image manquants.

Décisions : conserver le choix de mode ajouté simultanément dans le projet ; conserver les références sous item_id pour les homonymes ; extraction locale plutôt que téléchargement des images. Revue indépendante : trois défauts corrigés (variantes, icônes partagées, pied de formulaire sur petite fenêtre), couverts par tests. Pas de dépôt .git disponible dans cet espace ; modifications appliquées aux sources locales utilisées par le lanceur.

Validation finale : pytest 489 passed / 21 skipped, 42 sous-tests ; interface Windows dans deux processus indépendants : 9 + 5 tests réussis. Réduction de marges du tableau de bord après échec reproductible à 960×660, puis test corrigé. Test regroupant plusieurs racines Tk interrompu par une exception native Windows ; validation graphique isolée utilisée. Artefacts temporaires et journaux dans .test-tmp, sources et données dans Application.
