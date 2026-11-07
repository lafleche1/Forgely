# Référentiel indexé v22.03

Le moteur conserve les règles communes et les mêmes 322 cas effectivement relevés (17 états, 10 équipements). La recherche d'un relevé exact, des bornes et des limites utilise maintenant un index SQLite en lecture seule, au lieu de parcourir toute la référence JSON. Le contexte est préparé une fois pour comparer les runes d'un conseil.

## Mesures locales

Temps en millisecondes, médianes. Mesures du 7 novembre 2026 sur le même environnement Linux/Python ; elles ne prédisent pas exactement les performances de chaque PC Windows.

| Opération | Avant v22.01 | Après v22.03 |
|---|---:|---:|
| Rechercher une rune dans la base réelle | 0,072 | 0,032 |
| Produire un conseil dans la base réelle | 0,597 | 0,269 |
| Rechercher le dernier objet d'une fixture de 3 000 contextes, contexte répété | 9,021 | 0,032 |
| Produire un conseil sur cet objet, contexte répété | 54,698 | 0,270 |
| Produire un conseil pour un objet non encore en cache dans cette fixture | Non mesuré | 0,878 |

La fixture de croissance duplique un profil en objets fictifs pour tester la recherche, pas la validité d'une stratégie de forgemagie. Elle n'est ni installée, ni fusionnée avec les références, ni enregistrée dans les observations. Le dernier test change d'objet à chaque requête dans un processus déjà démarré ; ce n'est pas une mesure du démarrage complet de l'application ni d'un disque froid.

L'ancien benchmark utilisait 300 recherches et 100 conseils sur la base réelle, puis 20 recherches et 10 conseils sur le dernier objet de la fixture. Le nouveau utilise 300 recherches/100 conseils réels, 100 recherches/100 conseils répétés sur la fixture et 200 objets distincts. Les valeurs p95 et les mesures brutes figurent dans le JSON compagnon. L'ancienne version est le commit local 551f0a2, équivalent au code publié 286b7e1 avant indexation.

## Volume et mémoire

- Référence runtime : **77 824 octets (76 Kio)** contre 97 966 octets pour le JSON d'origine (environ 96 Kio).
- Fixture fictive de 3 000 contextes : environ 14,4 Mio sur disque. Ce fichier temporaire est supprimé après le test.
- Caches bornés : 32 objets et 64 contextes, y compris les recherches sans résultat.
- Après 200 lectures d'objets différents : environ **1,18 Mio d'allocations Python conservées par le lecteur**, pic 1,20 Mio. Cela exclut le reste de Forgely, les allocations natives SQLite et les données de préparation du benchmark. Ce n'est pas la mémoire totale du programme.

Les connexions de lecture sont fermées après chaque accès SQL. Le moteur ne charge ni la source JSON complète ni les 3 000 profils en mémoire. Les dossiers `references` et `docs`, avec le plan de collecte et les benchmarks, restent hors des ressources ajoutées par PyInstaller.

## Collecte utile

`dofocus-collection-targets.json` contient 64 entrées proposées, dédupliquées et réparties entre familles. Les dix premières ciblent des familles encore absentes des relevés. D'autres entrées explorent le reliquat autour du poids d'une rune, le voisinage du maximum, les paliers et le franchissement de zéro d'un malus. Ce sont des questions à tester dans Dofocus, jamais des règles nouvelles ou des pourcentages calculés.

Les nombres de références réelles ne sont pas gonflés par cette liste. Pour un état non relevé, Forgely continue à afficher l'absence de pourcentage disponible. Les observations du joueur, les prix personnels et le budget restent séparés.

## Reproduire

Depuis la racine du dépôt :

```bash
python Application/preparer_reference_dofocus.py
python -m pytest -q
python Application/mesurer_reference_dofocus.py --contexts 3000 --output mesures.json
python Application/preparer_collecte_dofocus.py --limit 64 --output collecte.json
```

Les 322 cas de la ressource empaquetée sont comparés à la source par les tests. Une référence manquante, corrompue ou d'un schéma incompatible rend les relevés indisponibles, sans taux de remplacement. Le constructeur valide la source puis remplace la ressource atomiquement. La fabrication Windows reconstruit cette ressource avant PyInstaller.

Cette optimisation concerne les conseils. Le temps de capture et de reconnaissance OCR n'a pas été amélioré par ce changement.
