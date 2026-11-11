# Jet cible prioritaire

Objectif confirmé : obtenir simultanément tous les minima demandés. Les prix
et budgets monétaires ont été retirés du calcul et des interfaces.

Choix : conserver le moteur hybride 60 % réel / 40 % simulation et corriger
l'apprentissage avant d'augmenter le volume. Une simple hausse du nombre
d'épisodes reproduirait la politique d'abandon. Une planification complète dans
DOFUS demanderait d'abord une validation des transitions du simulateur.

Implémentation : récompense terminale dominante pour le jet complet, progression
bornée servant de guidage, échec terminal sans récompense de progression,
apprentissage sans actualisation temporelle ni pénalité de prix et arrêt volontaire exclu tant
qu'une rune ciblée reste disponible. Seuls le stock et le nombre maximal de
poses contraignent les tentatives ; les anciens paramètres monétaires sont ignorés.
Les anciennes récompenses sont incompatibles avec les nouvelles politiques.

Activation : évaluation réservée, au moins 50 sessions par stratégie et borne
Wilson à 95 % de la politique supérieure à celle du témoin. Une politique non
concluante ou annulée reste sauvegardée mais inactive. Le chargeur revérifie les
résultats. Zéro simulation ne devient une observation réelle.

Limite : ce changement corrige l'objectif et filtre les politiques ; il ne
prouve pas une amélioration réelle dans DOFUS et ne constitue pas encore une
recherche exhaustive des suites de runes.


## Correction locale du 8 novembre 2026

Les cibles sont des minima : comme le copilote, l'environnement d'apprentissage
accepte un dépassement à l'intérieur des bornes naturelles connues. Cela ne
permet pas un over/exo non demandé. Un échantillonnage des états de chaque échec
remplace la capture tardive à mi-horizon ; le rejeu préserve le nombre de poses
restantes. Les graines d'apprentissage, de sélection et d'audit sont séparées.

L'évaluation passe à 200 sessions par défaut dans le moteur et l'interface.
Le seuil technique minimal de validation reste 50 ; une évaluation plus petite
peut servir au diagnostic mais ne valide jamais une politique.
La reprise et les conseils privilégient la meilleure archive compatible selon
la validation puis la borne basse Wilson de réussite du jet complet. Les
archives restent conservées. Le banc fixe de sélection ne prouve pas la
généralisation ; `Application/auditer_politique.py` permet un audit séparé,
figé, sans entraînement ni promotion automatique.

Voir le [rapport mesuré](RAPPORT_ENTRAINEMENT_2026-11-08.md).
