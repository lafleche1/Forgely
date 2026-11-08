# Sélection d'équipement et jet souhaité

Le parcours manuel approuvé est intégré : catégorie → objet avec icône et nom → valeurs cibles → démarrage. La détection automatique également présente dans le projet reste disponible via le choix de mode.

Les catégories utilisent les type_id du jeu, afin de traiter aussi les noms qui ne contiennent pas le type (Gelano, Makroute, etc.). Le catalogue local comprend 2 861 équipements et 2 695 icônes uniques. Le manifeste assets/equipment_icons/manifest.json constate zéro icône manquante. Les images proviennent du bundle local DOFUS 3 item_assets_1x.bundle, Unity 6000.3.16f1 ; aucun nom n'est déduit de l'image.

Les 17 502 lignes de caractéristiques naturelles supportées sont extraites des possibleEffects et de leurs métadonnées caractéristique/opérateur. Elles restent des références théoriques, jamais des jets observés. Les dégâts des armes et les effets non reconnus ne sont pas convertis. Le formulaire permet une saisie de cibles et l'ajout de caractéristiques ; une cible vide est ignorée et au moins une cible est requise. « Jet naturel maximum » remplit explicitement les maxima connus.

Les variantes partageant un nom gardent un identifiant de stockage distinct et des bornes par item_id. Les objectifs conservent cet item_id. Les anciennes références CSV personnelles restent prioritaires pour les noms correspondants ; les références embarquées servent de repli.

En mode manuel, l'OCR du nom et la recherche dans le catalogue visuel sont évités. L'icône actuelle et les lectures stabilisées du jet/puits restent nécessaires. Une contradiction avec les bornes de l'objet choisi bloque immédiatement l'association ; trois contradictions consécutives exigent une nouvelle sélection. Un changement d'icône, de profil, de compte ou la disparition d'un atelier déjà lié invalide la session manuelle. Une étiquette manuelle n'enregistre aucune référence de reconnaissance automatique.

L'outil de développement extract_equipment_assets.py permet de réextraire les ressources depuis une installation du jeu en lecture seule ; il requiert UnityPy==1.23.0. L'application n'a pas besoin de UnityPy ni d'Internet pour le sélecteur.

Validation ciblée : catalogue, recherche accent-insensible, variantes homonymes, bornes, cibles, changement d'objet, disparition de l'atelier et contradiction de profil. Tests Tk réels : catégorie/objet/cibles, annulation sans modifier la session, boutons accessibles à 800×600, enregistrement des objectifs, blocage du démarrage manuel sans sélection et absence d'apprentissage automatique des icônes manuelles.

La vitesse réelle de l'OCR et les conseils en partie ne sont pas mesurés par ces tests d'interface. Les sources locales sont mises à jour ; aucun exécutable distinct n'a été reconstruit.

Résultats de validation finaux : suite pytest standard, 489 réussites, 21 exclusions et 42 sous-tests réussis. Vérifications graphiques exécutées séparément sous Windows : test_dashboard_tk.py, 9 réussites ; test_equipment_picker_tk.py, 5 réussites et 10 sous-tests réussis. Compilation Python des modules modifiés réussie.

Le contrôle DashboardTkTests.test_small_window_keeps_table_pool_and_latest_reading_visible a d'abord détecté une table trop basse à 960×660 ; les espacements ont été réduits et les neuf tests du tableau de bord ont ensuite réussi. Une tentative regroupant toutes les classes graphiques dans un même processus a déclenché une exception native Tk/Windows 0xc0000008 pendant update ; les deux classes concernées ont été vérifiées dans des processus séparés. La suite standard conserve les tests graphiques désactivés par défaut.
