# Forgely

Application Windows d'assistance à l'observation de la forgemagie DOFUS.

## État du projet

Base de travail actuelle : **v21.02 — surveillance indépendante**. Le code source complet n'est pas encore importé dans ce dépôt.

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

## Confidentialité

Ne pas publier de captures contenant des informations personnelles, des identifiants, des journaux privés ou des secrets.
