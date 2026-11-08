# Dofocus, référence des conseils Forgely v22.03

**Actualisation du 8 novembre 2026 :** ce document conserve l’historique des
relevés de simulation. Les densités actives utilisent maintenant le référentiel
client versionné commun ([provenance et poids](POIDS_RUNES.md)). Les contextes
Dofocus restent séparés des observations réelles et ne certifient pas les taux
du jeu. Le protocole corrigé est décrit dans [les règles actives](REGLES_ACTIVES_FORGELY.md).

À la demande de l'utilisateur, les conseils actifs utilisent désormais Dofocus comme référence de base. Consultation du 7 novembre 2026. Le moteur principal, le résumé du plan et l'ancien point d'entrée de conseil partagent la même décision.

## Sources et périmètre

- Simulateur : https://dofocus.fr/forgemagie/
- Tableau des runes : https://dofocus.fr/guide/
- Origine des données : https://dofocus.fr/about/
- Conditions : https://dofocus.fr/terms/

Le guide concerne essentiellement le brisage. Focus et coefficient de brisage ne servent donc pas au calcul d'une pose de rune. Les poids du tableau et ceux affichés par le simulateur servent de référence ; le simulateur prévaut pour l'ambiguïté du texte sur la Vi : gain nominal +5, poids 1, soit 0,2 par point de vitalité. Les données économiques ne sont pas collectées.

## Règles utilisables et degré de preuve

| Élément | Utilisation dans Forgely | Preuve et limite |
|---|---|---|
| Gains et poids | Comparer les paliers disponibles, afficher le poids nominal | Tableau public et valeurs visibles du simulateur ; aucune probabilité dérivée du seul poids |
| Jet naturel | Distinguer une ligne naturelle, un dépassement et une ligne ajoutée | Bornes affichées pour les dix objets relevés ; les valeurs théoriques ne remplacent jamais l'OCR |
| Runes interdites | Exclure une pose qui dépasserait une limite explicitement affichée | Limites conservées avec objet et caractéristique ; aucune formule générale de plafond reconstruite |
| Malus | Signaler le coût réduit mentionné par le simulateur | Le franchissement de zéro n'est pas modélisé ; les conseils gardent le poids nominal conservateur |
| SC / SN / EC | Afficher les trois valeurs d'un état exactement relevé | Pourcentages de simulation, arrondis indépendamment ; ≈0 ne signifie pas zéro exact |
| Reliquat | Exiger une lecture confirmée et comparer au poids nominal | Pas de déduction du puits à partir du manque au jet parfait ; aucune promesse de passage |
| Difficulté | Relevés d'interface : palier 80 %, ×20, over, qualité et bas niveau | La formule complète n'a pas été obtenue ; aucune reproduction prétendument exacte |
| Prix et serveur | Les prix saisis par l'utilisateur restent séparés | Aucun cours Dofocus importé, aucun prix manquant remplacé par zéro |

Les explications du simulateur et le mini-test déjà réalisé (Fo sur Cycloïde : SN, +1 Force, −1 reliquat) sont des éléments de simulation. Ils ne constituent ni une preuve d'algorithme officiel ni une tentative réelle utilisée pour apprendre.

## Collecte réellement effectuée

17 états complets, 322 cas de rune dont les interdictions, 10 objets et 8 familles :

| Objet | Identifiant | États relevés |
|---|---:|---|
| Anneau du Comte Harebourg | 14077 | minimum, moyen, maximum ; puits 0 |
| Gelano | 2469 | PA 1 ; PA 0 ; PA 0/PM exo 0 ; PA 1/PM exo 0 ; puits 0 |
| Solomonk | 7143 | moyen ; puits 0 |
| Bottes du Strigide | 14096 | moyen ; puits 0 |
| Amulette Séculaire | 14080 | moyen ; puits 0 |
| Cape du Sinistrofu | 14085 | moyen ; puits 0 |
| Ceinture du Strigide | 14095 | moyen ; puits 0 |
| Baguette de Malléfisk | 15216 | moyen ; puits 0 |
| Bouclier du Captain Amakna | 18670 | moyen ; puits 0 |
| Anneau du Cycloïde | 14092 | moyen/puits 0 ; moyen/puits 10 ; Force 10 et autres lignes moyennes/puits 10 |

Les contrôles de recherche, préréglage, édition du jet et ajout d'exo ont été utilisés dans le navigateur. Les libellés accessibles des boutons de rune fournissent les valeurs. Les nombres ont été transcrits en données structurées et contrôlés. Aucun prix ni historique économique n'est enregistré. Le JSON auditable se trouve dans `Application/references/dofocus/reference.json`. La ressource embarquée en lecture seule est `Application/assets/dofocus/reference.sqlite3`.

Cette collecte est un échantillon, pas tous les objets du jeu, ni toutes les combinaisons de jets et de puits. Les règles de poids s'appliquent aux caractéristiques compatibles de n'importe quel équipement ; cela n'autorise pas à transférer les pourcentages entre objets ou jets. Les caractéristiques non couvertes sont laissées sans conseil de rune.

## Application aux conseils

1. Identification confirmée, jet actualisé et reliquat connu restent obligatoires.
2. La liste des runes et leurs poids vient du référentiel Dofocus.
3. Les paliers qui dépassent l'objectif ou une limite explicitement relevée sont exclus.
4. Un relevé chiffré n'est disponible que pour le même objet, le même jet complet (malus et exos compris), le même reliquat et la même rune. Une seule ligne différente, manquante ou supplémentaire désactive ce relevé.
5. Les valeurs affichées sont utilisées pour classer les candidats de cet état seulement. Le classement selon l'objectif et l'exposition au poids reste une politique Forgely, pas une stratégie publiée par Dofocus. Sans relevé exact, le choix est qualitatif et aucun taux n'est inventé.
6. L'ancien repère Huzounet à 1 % n'alimente plus les conseils actifs. Les anciens modules de recherche restent conservés comme archives distinctes.
7. Les gardes de plafonds par ligne et d'exos cumulés à 101 sont conservées depuis l'évolution des deux modes de recommandation, comme politiques Forgely distinctes des limites effectivement relevées chez Dofocus. Les overs de lignes différentes ne partagent pas un faux budget global. Une situation bloquée par une garde ne démontre pas une impossibilité dans le jeu.
8. Les observations locales restent descriptives, ne changent pas le modèle Dofocus et ne reçoivent aucune simulation comme tentative.

L'absence de formule complète empêche de reproduire les probabilités du simulateur pour un état inédit. Une collecte couvrant quelques objets ne permet pas de résoudre cette limite. Pour couvrir tous les équipements et tous leurs états avec le modèle Dofocus, il faudra une méthode publiée ou un export autorisé par son auteur. Aucun contact n'a été envoyé en votre nom.

## Maintenance

Les données sont lues hors ligne, par recherche indexée sur l'objet et le contexte exact. Le JSON d'auteur n'est pas chargé par le moteur ni inclus dans les ressources de l'exécutable. Les caches sont bornés à 32 objets et 64 contextes. Le validateur vérifie provenance, bornes, poids, unicité des contextes et cohérence des pourcentages arrondis. Un fichier absent ou invalide désactive les relevés chiffrés ; il n'entraîne pas de taux de remplacement. Toute extension doit garder la provenance, la date, l'objet, le jet complet et le puits.

## Intégration avec les deux objectifs

La version du dépôt a évolué en parallèle vers deux modes. Cette intégration conserve **Chances maximales**, **Budget optimisé**, les prix personnels, le coût des tentatives enregistrées depuis le lancement et le blocage d'un budget incomplet. Les pourcentages d'un état exactement relevé pondèrent la progression du candidat ; le mode économique conserve aussi sa comparaison de coûts. Aucun prix Dofocus n'est récupéré et la probabilité du jet final reste inconnue.


## Croissance de la base (v22.03)

Le constructeur `python Application/preparer_reference_dofocus.py` valide le JSON puis remplace atomiquement la base SQLite. La fabrication de l'exécutable le lance avant PyInstaller ; la CI vérifie que les 322 cas embarqués correspondent à la source. Une référence absente ou corrompue désactive les relevés chiffrés, sans toucher aux observations personnelles.

`python Application/preparer_collecte_dofocus.py --limit 64 --output collecte.json` prépare uniquement des entrées à vérifier dans le simulateur. La liste versionnée `docs/dofocus-collection-targets.json` privilégie les familles peu couvertes, répartit les questions entre familles et exclut les cas déjà relevés. Ces cibles ne sont ni des conseils de pose dans DOFUS ni de nouvelles données de réussite. Aucune collecte massive n'est lancée automatiquement.

Mesures et protocole : `docs/PERFORMANCES_REFERENCE_V22_03.md`.

