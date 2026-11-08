# Modèle vidéo prioritaire et calibration réelle

Le copilote utilise maintenant le modèle de la vidéo « J’ai cracké le secret de la forgemagie DOFUS », fournie par l’utilisateur, comme référence prédictive prioritaire. Source : écrans vers 6:55 et 9:00, 225 887 clics annoncés. Ce n’est pas une publication du code serveur.

## Ce qui est calculé

`Application/forgely_predictive.py`, version `video-2026-11-08-v2` :

- base D=5 ; +45 dès 80 % de la valeur actuelle/max naturel, y compris en over, selon la définition additive précisée par l’utilisateur ;
- over : +65 et +4 par point de densité de dépassement du jet proposé ; cette convention de franchissement est une reconstruction ;
- taille de rune : +12 × max(0, valeur actuelle / gain nominal de la rune −14) ;
- qualité : +60 Q^12 ;
- niveau connu inférieur à 170 : −20 max(0,1.1−Q). Niveau absent : bonus omis et avertissement. Le niveau optionnel 1–200 se renseigne dans l’éditeur des jets souhaités et est conservé par objet avec l’objectif ; il est transmis à tous les points d’entrée et au scénario SC. Aucun niveau n’est deviné ;
- SC : max(2,(100−D)/2), borné à 100 ;
- SN : reconstruction du premier écran, appliquée au score x=(100−D)/2 avant plancher : min(50,100−SC) si x≥0, sinon max(15,50−0.75|x|), puis −10 en over. Borné entre 0 et 100−SC ; EC=100−SC−SN.

Les deux écrans de la vidéo ne donnent pas une formule identique. Combiner le SC final et la forme antérieure du SN est un choix d’implémentation exposé dans les hypothèses, pas une transcription exacte d’un algorithme publié.

Q : moyenne arithmétique des ratios valeur actuelle / maximum naturel de toutes les lignes naturelles positives, conformément à la précision mathématique de l’utilisateur. Le poids unitaire se simplifie dans chaque ratio ; ce n’est donc pas un ratio des sommes de densités. Chaque ratio est borné à [0,1], puis leur moyenne est prise. Une ligne de maximum nul ne participe pas ; les malus ne sont pas modélisés. Un PA, PM ou PO positif absent du profil naturel complet impose Q=1 : aucun autre +60 n’est ajouté. Cette définition a été précisée par l’utilisateur après la vidéo et remplace le proxy initial pondéré. Un profil partiel est signalé, toutes ses lignes doivent néanmoins être lues ; aucune omission n’est convertie en zéro.

Exo sur ligne absente du profil complet et rune de poids >20 : référence communautaire préexistante 1 % SC, 0 % SN, distincte du plancher vidéo. Exos légers non documentés : repli sans taux. Malus : pas de nouvelle formule inventée. Le demi-poids sur malus et les fréquences de chute du PA ne sont pas convertis en lois universelles.

## Influence sur le conseil

Le SC+SN estimé pondère la progression vers les minima. L’exposition au manque de puits est pondérée par la probabilité non-SC. Le surplus naturel est rapporté au gain de rune plutôt qu’au minuscule écart restant : en mode Chances maximales une rune plus grosse peut être préférée si elle passe mieux tout en restant naturelle. La pénalité heuristique ×20 est désactivée lorsqu’une estimation vidéo est disponible, pour éviter de compter deux fois la pression de taille de rune. Le mode économique conserve les prix Tylezia, les dépenses de session et les arrêts de budget. Le coût de réparation reste un proxy, pas une espérance validée des lignes perdues.

Le modèle est prioritaire sur les relevés ponctuels Dofocus ; ceux-ci restent affichés séparément et servent de repli si l’estimation n’est pas calculable. Les anciennes API de benchmark descriptif restent compatibles ; le champ `prediction` porte les estimations actives. Ni probabilité d’atteinte finale ni coût minimal garanti n’est produit.

## Calibration automatique

Les nouvelles transitions sont marquées `calibration_verified=1` seulement si le profil naturel complet est documenté, toutes ses lignes sont présentes dans les lectures avant/après et l’audit des gains/pertes/puits est cohérent. Cela certifie une cohérence interne, pas une lecture OCR infaillible. Les anciens enregistrements restent à 0. Les SN/EC sans variation sont admis lorsque ces conditions sont satisfaites pour éviter de sélectionner uniquement les pertes visibles.

Le laboratoire regroupe séparément ces transitions par objet, rune, jet exact et puits exact. Après au moins 30 essais, les taux utilisés valent :

`P = (200 × P_modèle + 100 × nombre_résultats) / (200 + N)`

avec P exprimé en pourcentage. Poids réel = N/(200+N). Le seuil 30 et le prior 200 sont des paramètres prudents de Forgely, pas des constantes de la vidéo ni des garanties statistiques. Les taux calibrés peuvent s’écarter du plancher du modèle. Les simulations ne sont jamais insérées dans les observations. Un cache avant-événement conserve le dernier état confirmé lors d’une variation avant l’arrivée de la ligne d’historique ; il expire après 8 frames et est réinitialisé lors des changements d’identité/session. La base locale conserve les comptages ; le calcul de classement n’écrit pas en base.

Pour les objets sans profil complet documenté ou avec lecture partielle, pas de calibration : modèle approché si les données suffisent, sinon ancien classement. Cette restriction réduit la couverture mais empêche de présenter tous les anciens clics OCR comme des données fiables.

## Vérification et limites

Les tests portent sur les seuils, les exceptions, la normalisation des trois taux, le branchement du conseil, la migration SQLite, la séparation des contextes et l’affichage. La comparaison avant/après démontre un changement de décision, pas une amélioration mesurée en jeu. Le gain réel devra être évalué sur des sessions réelles indépendantes (calibration des taux, coût et atteinte du jet cible). Aucun test natif Windows ni exécution du nouvel EXE depuis cet environnement.

## Installation Windows

Extraire tout le paquet cumulatif puis lancer `INSTALLER_MISE_A_JOUR_LOCALE.bat`. Il détecte les dossiers candidats immédiats ou ouvre un sélecteur de dossier. Le programme utilise le Python de l’installation choisie si disponible, puis le lanceur Python système. L’outil vérifie toutes les empreintes avant remplacement, sauvegarde les sources et refuse les versions locales inconnues. Les bases de données et préférences ne font pas partie du paquet.

Relancer avec `LANCER_FORGELY_MIS_A_JOUR.bat`, ajouté au dossier cible : cela lance le code source actuel plutôt qu’un EXE ancien. Aucun exécutable Windows n’est reconstruit ou remplacé. L’application doit être fermée pendant la mise à jour ; l’installateur ne tue pas les processus et ne lance pas de téléchargement. Les scripts Windows doivent encore être validés sur un PC Windows ; le moteur de remplacement est testé ici.

## Simulations dynamiques

Le laboratoire et le bouton de simulation utilisent maintenant ce modèle après chaque rune ; les transitions inconnues sont distinguées des pertes approximatives. Voir [SIMULATEUR_DYNAMIQUE.md](SIMULATEUR_DYNAMIQUE.md) et [RECHERCHE_PERTES_FM.md](RECHERCHE_PERTES_FM.md). Les simulations restent séparées des observations réelles.

## Bilans et expérience réelle

Le bouton de clôture produit un bilan local avec journal prospectif et comparaison des prévisions. Les nouvelles transitions qualifiées alimentent la calibration existante sans réimport du bilan. Voir [BILAN_SESSIONS_APPRENTISSAGE.md](BILAN_SESSIONS_APPRENTISSAGE.md).
