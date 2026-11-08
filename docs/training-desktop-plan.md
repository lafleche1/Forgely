# Entraînement accessible par double-clic

Livrable : `Entrainement_Forgely.exe` autonome, dans le dossier Forgely. Interface Tk native : recherche d'objet, objectifs éditables, jet de départ, sessions, horizon, prix facultatifs, progression, arrêt avec sauvegarde et accès aux résultats.

Le moteur existant reste inchangé. Un entraînement Q-learning avec état discrétisé est comparé à une référence heuristique sur des épisodes distincts. Les limites de discrétisation et de simulation sont explicites. Les politiques restent expérimentales et ne remplacent pas automatiquement les conseils en jeu.

Les conseils croisent désormais les sources à poids fixes : 40 % simulation et 60 % observations réelles comparables. Le signal appris et les pertes virtuelles restent dans la part simulation. Les facteurs relatifs d'expérience sont ramenés à la même échelle avant mélange. Une source absente est signalée, sans inventer d'observations ; la source disponible est utilisée provisoirement seule. Les politiques sans prix/budget peuvent être lues en arrière-plan pour un objet, modèle, profil et objectif compatibles ; les politiques économiques restent consultables dans leurs rapports.

Étapes :
1. Tester et écrire le contrôleur d'entraînement, validation, annulation et sauvegarde reproductible (JSON sans pickle), reprise compatible et évaluation hors entraînement.
2. Construire l'interface, sans traitement long sur le thread Tk. Résultats dans `Entrainements` à côté de l'exécutable ; cas erronés expliqués dans la fenêtre.
3. Tester l'interface et le contrôleur. Construire l'exécutable PyInstaller depuis les paquets officiels, avec les référentiels embarqués.
4. Exécuter un entraînement court depuis l'exécutable et vérifier la fenêtre réelle. Relire les changements et exécuter la suite du projet.
