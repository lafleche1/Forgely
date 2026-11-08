# Protocole expert corrigé

Autorisation : l'utilisateur demande d'intégrer la combinaison corrigée des deux
prompts proposée dans la réponse précédente, de détecter les conflits avec les
règles existantes et de lui donner ensuite les règles réellement appliquées.

Approche retenue : étendre le moteur Python et son affichage, sans moteur LLM ni
nouveau simulateur inventé. L'alternative consistant à stocker les prompts bruts
n'aurait aucun effet exécutable et introduirait des contradictions.

Objectif : minima du jet utilisateur, puis coût en mode Budget optimisé ; aucun
objectif implicite de revente ou de jet parfait. Terminer les remontées naturelles
ciblées disponibles avant de proposer une finition over/exo. Ne pas sacrifier
automatiquement une ligne, ne pas plafonner le reliquat à 101, conserver les poids
du référentiel actuel et les prix Tylezia. Les lignes non modélisées restent exclues.

Le détail du conseil affiche état du puits, action, phase, branches SC/SN/EC,
risque qualitatif et statut des données. Après un SC hypothétique, une seule
recommandation peut être recalculée sans perte, avec déduction du coût au budget.
SN/EC : pertes inconnues, pas de prochaine rune ou de puits numérique inventés.
Après toute pose réelle, attendre la lecture confirmée avant le prochain conseil.
Le dernier contexte avant/après peut expliquer les variations lues sans certifier
une comptabilité exacte quand le jet complet n'est pas garanti par l'OCR.

Les séries d'échecs ne déclenchent ni coefficient serveur ni probabilité nouvelle.
La probabilité d'atteinte finale reste inconnue. L'observation passive ne conseille
jamais de rune. Ne toucher ni aux observations ni à l'entraînement.

Livrables : code et tests, protocole lisible, inventaire exhaustif des règles
actives avec table des poids, rapport des conflits avec localisations exactes,
publication GitHub et paquet de mise à jour locale protégé par empreintes.

Demande complémentaire : rechercher les poids sur des références officielles.
Les accès directs Ankama ont échoué ; ne pas prétendre disposer d'une table
officielle vérifiée. Le référentiel est mis à jour à partir d'une extraction
indépendante du client 3.7.13.17 dont les deux fichiers source sont vérifiés par
SHA-256. Indiquer explicitement cette provenance et un statut non certifié éditeur.
Les 105 entrées sont couvertes : 103 ordinaires, Chasse spéciale, Signature hors
combat. Les réponses exploratoires DofusDB ne sont pas redistribuées.
