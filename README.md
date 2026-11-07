# Forgely

Application Windows d'assistance à l'observation de la forgemagie DOFUS.

## État du projet

Sources importées : **v21.02 — surveillance indépendante**. Version de développement : **v21.04 — variations rapides et diagnostic des lectures manquantes**.

Lancer `OUVRIR FORGELY.bat` sous Windows, ou `python Application/forgely.py` avec les dépendances de `Application/requirements.txt` et Tesseract installés.

La lecture rapide lit uniquement l'historique et la rune dans un thread dédié. Un résultat affiché « à vérifier » est provisoire : il ne crée aucune observation en base et ne guide pas les conseils. L'observateur complet conserve sa validation indépendante. Voir [le bilan technique](docs/IMPORT_OCR_V21_03.md).

La v21.04 affiche également les variations signées d'un historique sans résultat SC/SN/EC, sans tenter d'en déduire une rune ou une tentative. Dans ce mode, elle ne lance que l'OCR historique. Le diagnostic signale les noms de rune absents, les résultats non explicites et les retards. Voir [les corrections issues du diagnostic terrain](docs/OCR_V21_04.md).

### Objectif prioritaire

Afficher les résultats des runes en **moins d'une seconde**, sans perdre les événements et sans certifier les lectures ambiguës.

### Observations v21.02

- 504 captures inchangées évitant l'OCR ; 14 changements visuels.
- 11/11 caractéristiques reconnues sur Anneau du Cycloïde.
- OCR atelier médian : 2210,7 ms ; cycle médian : 4329,5 ms.
- 14 OCR sur images âgées de plus d'une seconde.
- Reliquat contradictoire : `4,5` / `45`.
- Historique : 0 lot confirmé, 4 transitions incertaines.

## Développement

Conserver la surveillance rapide (120 ms) et découpler l'OCR de l'historique, des caractéristiques et du reliquat. Ajouter des tests de non-régression avant toute publication de version.

Tests : `python -m pip install -r requirements-dev.txt`, puis `python -m pytest -q` depuis la racine. Les tests OCR nécessitent Tesseract ; certaines captures de référence privées ne sont pas fournies.

**Le délai inférieur à une seconde reste à mesurer dans DOFUS sous Windows.** Les mesures v21.02 ci-dessous ne constituent pas un résultat v21.03.

## Confidentialité

Ne pas publier de captures contenant des informations personnelles, des identifiants, des journaux privés ou des secrets.

