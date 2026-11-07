# Import et corrections OCR — v21.03

## Sources

Base : archive `Forgely-v21.02-surveillance-independante(2).zip`.
Application Windows Python/Tkinter, capture HWND/mss, OCR Tesseract local.
Les ressources des runes, catalogues CSV, installateurs et tests sont conservés.
Les historiques GitHub existants restent les parents de l'import.

Exclus : caches Python, bases locales, journaux, diagnostics privés, captures temporaires, répertoires pytest et fichier graphique `forgely_original.png` non référencé par le programme. La seule capture de test importée contient une table de caractéristiques sans identité de joueur.

## Corrections

- **Confirmation après changement :** le consommateur demande une nouvelle capture à la cadence de 120 ms ; il n'attend plus le rafraîchissement au repos de 12 secondes. Le cache d'historique est invalidé pour effectuer une seconde lecture OCR réelle.
- **Affichage rapide :** un thread indépendant lit seulement historique et rune. Deux lectures stables restent nécessaires. Le résultat « à vérifier » ne crée aucune observation, aucun conseil ni statistique. L'analyse complète conserve sa validation et son enregistrement habituels.
- **Contexte :** fermeture, perte de visibilité, arrêt, nouvelle session, compte différent ou icône différente invalident les aperçus. Un événement complet ancien reste enregistré mais n'écrase pas un aperçu plus récent.
- **Caractéristique absente :** un échec de recherche de première ligne est mémorisé huit secondes, pour les seuls pixels identiques. Cache borné à 32 signatures. Tout changement de pixels déclenche une nouvelle tentative.
- **Identification :** un nom complet inconnu n'est plus promu en nom officiel via le rapprochement réservé aux suffixes tronqués. Le cas d'objet anonyme n'utilise plus une variable inexistante dans le traitement des messages Tk.
- **Tests historiques :** alignement sur le recadrage explicite des icônes, les ressources officielles des runes, les deux variantes OCR par ligne et le refus des reliquats négatifs.
- **CI :** chemins pytest explicites, installation des dépendances Python et de Tesseract avant les tests.

## Mesures et validation

Validation locale finale : **297 tests réussis, 6 ignorés, 19 sous-tests réussis** ; **129 fichiers Python compilés**. Exécution Python 3.12 / Pillow 11.3.0, compatible avec la plage de dépendances du projet. Commande : `PYTHONPATH=../deps PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` (le préfixe `../deps` est propre à l'environnement de travail ; une installation normale utilise simplement `python -m pytest -q`).

**Validation GitHub Actions réussie** sur Python 3.11 avec Tesseract : [exécution 42339224322](https://github.com/lafleche1/Forgely/actions/runs/42339224322), commit source `33b6cc44ee8874f4a630ba29cf756d3df3d84aaa`. Installation, compilation et tests sont terminés avec succès. Les 449 fichiers envoyés ont été comparés aux empreintes Git distantes sans différence ; le diagnostic préexistant est conservé.

Les tests couvrent les transitions répétées, la conservation des pertes/gains, les conflits de reliquat, l'absence d'invention de valeur, les aperçus sans écriture en base, leur ordre d'affichage et l'invalidation de contexte.

Micro-mesure locale, sur une image synthétique uniforme sans ligne lisible : recherche initiale de première ligne **1341,13 ms** ; nouvelle demande avec les mêmes pixels **0,60 ms**. Cette mesure isole le cache des échecs ; elle ne mesure pas une rune réelle.

Le diagnostic expose `historique_et_rune` et `capture_vers_affichage` pour la lecture rapide. Cette dernière mesure part de la capture de confirmation : elle ne prouve pas à elle seule le délai entre l'apparition de la rune dans DOFUS et son affichage.

**Objectif inférieur à une seconde non encore validé.** Il faut mesurer une session réelle DOFUS sous Windows. Les six tests ignorés nécessitent des captures privées absentes de cette archive. Les interfaces déplacées ou redimensionnées peuvent désactiver la lecture rapide ; l'observateur complet reste disponible. Des historiques entièrement identiques, sans déplacement visuel observable, ne permettent pas de certifier des tentatives supplémentaires.

## Vérification sur Windows

1. Ouvrir un atelier avant Forgely, avec un historique déjà présent : aucun ancien résultat ne doit être compté comme nouvel événement.
2. Passer des runes différentes puis plusieurs runes identiques ; comparer chaque nouvelle ligne au nombre d'événements.
3. Changer d'objet, de compte, masquer DOFUS puis arrêter/redémarrer l'observation : aucun aperçu ancien ne doit revenir.
4. Exporter le diagnostic et comparer les métriques rapides et complètes. Pour mesurer rune → affichage, filmer simultanément les deux fenêtres ou utiliser un repère d'apparition indépendant.
