# Version complète à restaurer

Pour récupérer toute la version locale (sources, prix, ressources, historique des
simulations et exécutable Windows), télécharger le dépôt GitHub au format ZIP,
le décompresser puis double-cliquer sur `OUVRIR_VERSION_COMPLETE.bat` à la racine.

L'archive complète est transportée en morceaux d'un mégaoctet pour éviter les
limites du connecteur sur les gros fichiers. Le programme de restauration vérifie
l'empreinte SHA-256 de chaque morceau puis celle de l'archive complète avant de
l'extraire dans un **nouveau dossier**. Aucun dossier de travail existant n'est
remplacé. Dans ce dossier, lancer `OUVRIR FORGELY.bat` pour le copilote ou
`Entrainement_Forgely.exe` pour l'entraîneur.

Les environnements Python, les fichiers temporaires et les bases d'observations
personnelles ne sont pas transportés. Les historiques d'entraînement contenus
dans l'archive sont des simulations, pas des observations réelles.
