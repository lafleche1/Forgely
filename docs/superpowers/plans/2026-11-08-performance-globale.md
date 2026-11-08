# Réduction des latences Forgely

Autorisation : accélérer toute la chaîne sans affaiblir les confirmations ni les gardes OCR.

Mesures avant sur Linux/Python, données fictives : recherche dans 2001 noms ~81ms p50 ; lecture des bornes CSV10000lignes ~70ms ; conseil avec30000observations ~27ms. Les mesures sont des latences de fonctions locales, pas un temps réel Windows en jeu.

- [x] Indexer les noms normalisés et les candidats par longueur, en préservant ambiguïtés, doublons et correction floue.
- [x] Indexer les bornes naturelles par signature du fichier ; aucune valeur périmée après remplacement et aucune mutation du cache exposée.
- [x] Lire les statistiques de toutes les runes en une requête, ajouter un index SQLite couvrant ; ne pas lire le budget quand il est illimité.
- [x] Réutiliser un conseil pour un état EXACT identique, cache borné invalidé sur configuration, base/WAL, laboratoire, profil et audit ; ne pas figer un conseil après une fusion.
- [x] Précompiler les motifs du jet et des runes, réutiliser les parsings immuables bornés. Ne pas réutiliser un résultat OCR sur pixels différents.
- [x] Ne pas republier inutilement les mêmes widgets ; conserver l'ordre des événements et les contrôles de capture.
- [x] Éviter de reconstruire le laboratoire quand aucune donnée n'a changé ; exposer une révision pour invalider les conseils.
- [x] Tests d'invalidation, parité des résultats, mesures après, revue, suite complète, GitHub et paquet local cumulatif.

Les trois workers OCR et la limite OpenMP1 existent déjà. Aucune baisse arbitraire des confirmations, des seuils visuels ou de l'intervalle de capture n'est prévue. L'OCR natif Windows ne peut pas être chronométré ici.
