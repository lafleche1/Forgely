# Sessions vidéo dans l’entraîneur Forgely

## But et choix acceptés

Importer des sessions réelles MP4 dans l’entraîneur existant, reconnaître les tentatives, produire des rapports par objet et améliorer Forgely à partir des observations fiables. L’utilisateur a choisi l’intégration à l’entraîneur actuel. Aucun traitement audio : ni transcription, ni reconnaissance sonore, ni dépendance audio.

## Approches

1. Onglet intégré à l’entraîneur : aperçu, analyse, vérification et rapports au même endroit. Choix de l’utilisateur, recommandé pour partager le catalogue et éviter plusieurs applications.
2. Application vidéo indépendante : isolation plus simple mais parcours et réglages dupliqués. Non retenue.
3. Feuilles CSV manuelles actuelles : conserver comme export et secours, insuffisant pour l’analyse automatique demandée.

## Parcours proposé

Ajouter deux onglets : « Sessions virtuelles » (fonctionnement actuel préservé) et « Sessions vidéo ». Dans le second : ajouter un ou plusieurs MP4, afficher durée/résolution et aperçu, régler au besoin les zones objet, jet, rune et journal sur une image. Conserver les zones en coordonnées relatives par profil de disposition ; ne pas présumer qu’une disposition convient à toutes les vidéos.

Boutons Analyser, Arrêter, Reprendre, Voir le rapport et Transmettre les observations fiables. Traitement hors du fil graphique, progression et fichier courant visibles. Arrêt propre avec sauvegarde. L’aperçu permet de naviguer aux instants détectés, de comparer avant/après, de corriger ou rejeter une lecture. L’ajout d’une vidéo n’efface ni les résultats précédents ni les apprentissages virtuels.

## Analyse visuelle

Décodage local avec OpenCV déjà utilisé par laboratoire_videos.py. Échantillonnage adaptatif : passage peu coûteux pour les changements, puis lecture plus fine autour des événements. Réutiliser les lecteurs OCR, catalogue, références de runes et contrôles de transitions existants via des adaptateurs indépendants de la capture écran. Ne pas traiter toute variation visuelle comme une fusion.

Pour une tentative : identifier l’objet et son profil naturel, la rune effectivement utilisée, un événement de résultat et des jets stables avant/après. Synchroniser ces éléments dans une fenêtre temporelle courte, réinitialiser lors des changements d’objet et discontinuités. Aucun résultat inventé à partir des seules différences de caractéristiques. Gérer les tentatives sans changement visible avec preuve d’événement distinct ; une ligne de journal persistante ne constitue pas une nouvelle tentative. Si plusieurs essais ont lieu entre deux lectures fiables, conserver une séquence ambiguë sans la convertir en essai unique.

Détecter coupes, zooms, changements de disposition, journal absent, lignes masquées et fins de vidéo. Suspendre l’appariement à ces frontières. L’objet peut être confirmé manuellement quand la reconnaissance échoue. Les caractéristiques absentes restent inconnues, pas zéro. Le puits initial inconnu reste inconnu : une cohérence comptable seule ne prouve pas sa valeur. Une vidéo accélérée ou illisible peut fournir un rapport partiel, sans garantie d’exhaustivité.

## Qualification et rapports

Statuts explicites : candidat, incomplet, ambigu, cohérent automatiquement, confirmé par l’utilisateur, rejeté. « Cohérent automatiquement » indique des contrôles satisfaits et non une vérité certifiée ; un score OCR seul ne suffit pas. Conserver images de preuve, texte OCR brut, raisons de qualification et corrections. Chaque événement conserve identité de vidéo, temps, objet, rune, résultat, jets, puits connu/inconnu, version des lecteurs et profil.

Contrôler les poids depuis la table partagée, le gain nominal de la rune et la comptabilité des pertes. SC conserve le puits. SN/EC dépendent des pertes réellement mesurées et du poids tenté. Une perte d’over n’accorde pas automatiquement tout son poids en puits. Ne pas imposer de stratégie universelle ni de taux serveur supposés.

Rapport HTML local et JSON/CSV : résumé de couverture et limites, nombres acceptés/ambigus/rejetés, fréquences SC/SN/EC par objet/rune/contexte avec effectifs et incertitude, pertes/consommation observées, évolution du jet et du puits connu. Distinguer observation d’une stratégie et preuve qu’elle améliore les résultats. Objectifs inconnus signalés : ne pas appeler « mauvaise décision » une action sans connaître le jet recherché.

## Transmission à Forgely

Stockage de revue distinct sous Entrainements/Videos ; les vidéos originales restent à leur emplacement. Identifiant fondé sur le contenu du fichier, événements stables et import idempotent : réimporter, déplacer une vidéo ou reprendre ne double pas les observations. Une correction conserve son historique et remplace sa contribution précédente lors du recalcul, sans compter les deux versions.

Un clic transmet les observations qualifiées au stockage empirique partagé ; les cas complets cohérents peuvent contribuer automatiquement à ce lot, les ambiguïtés nécessitent correction. La base actuelle fusion_contexts impose source=local_screen : ne pas maquiller une vidéo en capture directe. Ajouter une voie de stockage vidéo versionnée et un lecteur commun d’observations qualifiées, ou une migration conservant la provenance. Préserver les données existantes.

Calibration uniquement avec profil et contexte complets et comparables, effectifs visibles et seuils conservateurs existants. Apprentissage indépendant par objet, avec contexte rune/jet/puits et identité naturelle. Les simulations et observations restent identifiables séparément. Une vidéo ne remplace pas directement une stratégie active : ses observations servent à calibrer le modèle puis à comparer les stratégies sur des essais distincts. Ne pas promettre une amélioration tant que la comparaison n’a pas établi un gain.

## Contraintes et décisions du constructeur

Tout fonctionne localement, aucune mise en ligne des MP4, aucun clic dans le jeu. Première version pour vidéos où atelier et journal sont suffisamment visibles ; réglage manuel des zones si nécessaire. Pas d’extraction YouTube, pas de compréhension générale par un modèle distant. Utiliser Python/Tkinter et les composants installés. Les choix de disposition détaillée, fréquences d’échantillonnage et seuils sont laissés au constructeur, à documenter et mesurer ; aucun taux de reconnaissance annoncé sans corpus réel annoté.

La validation commence avec vidéos synthétiques contrôlées : décodage, recherche temporelle, annulation/reprise, déduplication, appariement, qualification, corrections et stockage. Vérifier l’interface à plusieurs tailles et l’absence de régression de l’entraîneur virtuel. Une session réelle représentative fournie par l’utilisateur est nécessaire pour mesurer la qualité de reconnaissance en conditions réelles ; son absence ne doit pas bloquer la construction ni justifier une prétendue validation réelle.

## Périmètre de livraison

Développement et essais locaux, conservation des ajouts existants. Pas de nettoyage, remplacement des archives distribuées ou publication GitHub de cette nouvelle fonctionnalité sans demande correspondante. Les essais sur les overs et l’intégration des principes FM justes restent des travaux à terminer ; ce projet vidéo ne les annule pas.
