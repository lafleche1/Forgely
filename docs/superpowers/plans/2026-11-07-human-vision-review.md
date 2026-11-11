# Confirmation manuelle des lectures

Objectif : collecter les zones de lecture inconnues de la V1 pendant l'observation,
permettre confirmation/correction/illisible, et constituer des références réutilisables.

Décisions : Python/Tk et stockage SQLite local, sans nouvel appel réseau. File
non modale accessible depuis le tableau de bord et Outils. Aucun popup pendant
une rune. Déduplication sur masque et échelle, limite de 100 candidats en attente.
Les suggestions OCR ne sont pas des étiquettes validées. La correction concerne
une image archivée, jamais le jet vivant au moment du clic.

Références numériques : l'utilisateur sélectionne le rectangle du nombre et du
libellé pour éviter d'apprendre les icônes ou colonnes Min/Max. Transcription
numérique stricte, segmentation univoque, vérification de reconstruction. Les
glyphes ne sont activés qu'après deux images confirmées distinctes concordantes.
Toute contradiction désactive la forme concernée. Une référence peut être
désactivée depuis l'interface. Les références sont partagées entre objets d'une
même échelle et ne mémorisent pas une valeur permanente d'objet.

Collecte : lignes des effets + reliquat. La lecture de l'historique reste au
moteur actuel ; une validation de glyphes ne certifie jamais une tentative FM.
Les références validées sont consultées en parallèle de l'OCR existant et leurs
lectures sont exposées au diagnostic ; aucun remplacement silencieux du moteur
de conseils avant évaluation terrain.

- [x] Tests et stockage : doublons, persistance, limite, illisible, contradictions.
- [x] Tests et références : segmentation/boîtes, valeurs variables, zéro et décimales,
  séparation des échelles, activation sur exemples distincts, désactivation.
- [x] Collecteur borné et intégration au worker : captures ciblées uniquement.
- [x] Interface de confirmation et compteur, reconstruction de référence.
- [x] Tests complets, revue et documentation d'utilisation.

Précisions demandées pendant l'implémentation : l'éditeur est un Frame dans le
panneau flottant existant, sous le conseil ; aucune nouvelle Toplevel de
vérification. La fenêtre passe de 370x510 à 570x640 pendant l'édition puis se
replie. La carte de l'objet automatique et son éditeur de jet cible suivent
l'identité confirmée, sans réutiliser l'objectif d'un autre objet.

Validation : 1 394 tests réussis, 24 ignorés et 42 sous-tests dans la suite
complète ; test supplémentaire du reliquat réel 1,9 réussi ; test d'interface
de l'éditeur automatique exécuté séparément et réussi. Régression réelle
40 Intelligence ajoutée pour l'arrondi de matchTemplate, suivie d'un XOR exact.
