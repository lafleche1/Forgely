# Forgely

Les 105 prix Tylezia envoyés depuis le téléphone sont intégrés au mode **Budget optimisé**, sélectionnable dans les paramètres. Les poids des runes sont partagés et le détail du conseil expose les scénarios conditionnels SC/SN/EC. Voir [les prix et leurs limites](docs/PRIX_RUNES_TYLEZIA.md) et [les poids](docs/POIDS_RUNES.md).

Version source 22.15 : matrice de décision par phase de puits, estimations théoriques
explicitement identifiées, deux scénarios et suivi exact du puits sous continuité vérifiée.
Le profil sélectionné manuellement est associé dès la première
lecture, sans recommencer la stabilisation après confirmation de l’icône.
Objet et cibles conservés après une rune, affichage
« Actualisation du jet » et captures rapprochées pour reprendre les conseils.
Validation toujours visible dans l’éditeur flottant,
ouverture à droite et retour du focus à DOFUS après enregistrement.
Case à cocher « Jet parfait », qui applique toutes les
valeurs maximales théoriques de l’objet identifié ou sélectionné.
Jet souhaité directement dans le copilote dès la lecture stabilisée,
conseils sans attendre le nom de l’objet, association accélérée et calibration automatique
contrôlée, lignes de vérification complètes et guidage par le référentiel
théorique. La V1 complète les lectures OCR manquantes et refuse les contradictions.
Voir [le fonctionnement et les limites](docs/Verification_Visuelle_Manuelle.md).

Apprentissage du jet cible : le jet complet est prioritaire. Les politiques
annulées, insuffisamment évaluées ou sans gain démontré sur le témoin restent
sauvegardées mais inactives dans les conseils. Les anciennes politiques sont
conservées et incompatibles avec la nouvelle récompense. Voir
[le fonctionnement et ses limites](docs/JET_CIBLE_PRIORITAIRE.md).
Correction locale du 8 novembre : entraînement ciblé sur les échecs courts, conservation
de la meilleure archive, 200 évaluations par défaut et audit indépendant reproductible.
Voir [le rapport mesuré](docs/RAPPORT_ENTRAINEMENT_2026-11-08.md).
Une politique compacte peut maintenant apprendre un classement qui généralise aux
situations inédites ; voir [la seconde campagne](docs/RAPPORT_GENERALISATION_2026-11-08.md).
Cette option expérimentale reste désactivée par défaut après un audit sans gain.
Son gain direct et son autorisation dans le copilote sont évalués séparément.

Application Windows d'assistance à l'observation de la forgemagie DOFUS.

Le conseil poursuit un seul objectif : **atteindre le jet souhaité**. Les prix,
budgets et coûts en kamas sont retirés de l'interface et du calcul, y compris
dans l'entraînement. Les anciens paramètres économiques sont ignorés.
Le classement reste explicable, sans taux de réussite inventé.

Capture et OCR optimisés : requêtes identiques mutualisées, récupération des lignes
réutilisée sur pixels inchangés, affichage plus réactif et isolation renforcée des
sessions. Voir [les mesures et limites](docs/PERFORMANCE_OCR.md).

## État du projet

Sources importées : **v21.02 — surveillance indépendante**. Version de développement : **v22.00 — le nouvel atelier émeraude**.

Nouvelle interface : navigation latérale, tableau du jet actuel et des cibles, assistance dédiée, puits visible, fil de lecture et mode flottant redessiné. Les observations provisoires sont indiquées comme telles ; aucune valeur de démonstration n'est ajoutée. Les outils existants restent accessibles dans la rubrique Outils. Voir [la refonte v22](docs/INTERFACE_V22.md).

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



## Sélection de l'équipement et du jet souhaité (v22.05)

Choisir « Sélection manuelle », puis la catégorie (Coiffe, Cape, Anneau,
Amulette, Ceintures, Bottes ou Arme), l'objet et ses valeurs cibles.
Le formulaire présente les bornes naturelles disponibles, propose « Jet naturel
maximum » et permet d'ajouter une caractéristique, notamment pour un exo.
Une case vide signifie que cette caractéristique n'est pas un objectif.

Le catalogue contient 2 861 équipements et 2 695 icônes distinctes, extraites
localement de l'installation DOFUS 3. Les sept catégories ont toutes leurs
images. Aucun téléchargement n'est requis pour utiliser le sélecteur.

En sélection manuelle, le nom choisi remplace l'identification OCR du nom.
Le jet actuel et le puits continuent à être lus et stabilisés dans DOFUS.
Un changement d'objet détecté ou un profil naturel incompatible suspend
l'association. Les noms choisis manuellement ne deviennent pas des références
de reconnaissance automatique.

Voir docs/SELECTION_EQUIPEMENT.md pour les données et la validation.
