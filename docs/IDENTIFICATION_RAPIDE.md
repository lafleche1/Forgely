# Identification accélérée — 7 novembre 2026

L'identification reste obligatoire. La reconnaissance d'une référence nommée de l'icône actuelle, avec contrôle de compatibilité des bornes observées, précède désormais l'OCR du nom. Un résultat visuel connu évite les deux passes OCR ; une icône inconnue ou ambiguë conserve le parcours OCR existant.

La stabilité du nom et de l'icône est vérifiée simultanément : trois captures cohérentes au lieu de cinq dans le parcours nominal. Les seuils de ressemblance, le contrôle des bornes et la remise à zéro au changement d'objet sont conservés.

Validation : 3 nouveaux tests réussis, dont le parcours réel du gestionnaire de messages confirmant à la troisième capture. 14 tests existants ciblés réussis. Compilation Python réussie.

Vérification élargie avec unittest : 349 entrées dans Application/tests et 47 dans Tests ; 377 réussites, 15 exclusions et 4 erreurs d'import dues à pytest absent :
- test_fm_context_values
- test_fm_objectives
- test_ocr_backend_performance
- test_ocr_regions_performance

La commande pytest complète n'a pas pu être exécutée. L'installation de pytest a échoué faute de résolution réseau. Les tests nécessitant des fichiers temporaires ont été relancés dans le répertoire de travail et Tesseract ajouté au PATH des processus de test.

Aucune mesure de latence réelle en jeu n'a été effectuée. Aucun exécutable n'a été reconstruit ; les modifications concernent les sources utilisées par le lanceur local.
