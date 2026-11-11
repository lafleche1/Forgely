# Règles harmonisées — état après correction du 8 novembre 2026

Ce document remplace l’état technique décrit dans l’audit précédent. Corrections locales, sans nouvelle publication GitHub et sans clic automatique dans le jeu.

## Une base commune

Le conseiller, le simulateur actif et l’entraîneur utilisent `forgely_fm_model`, version **forgely-unified-fm-2026-11-08-v1**. Le précédent calcul public Dofocus est conservé dans un module de référence historique, uniquement pour vérifier ses anciennes captures de test ; aucun chemin actif ne l’utilise comme moteur.

Les coefficients déjà documentés du modèle prédictif sont partagés : Q est la moyenne des remplissages naturels, seuil de 80 % sur la valeur actuelle, effet de la taille, surcharge, qualité et niveau. Les exos lourds utilisent une même référence communautaire de 1 %, jamais annoncée comme une probabilité serveur officielle. Les exos légers possèdent une courbe provisoire commune. SC, SN et EC ne sont donc plus calculés différemment entre affichage et entraînement pour un même contexte.

Les captures historiques Dofocus restent consultables comme références descriptives. Elles ne remplacent plus silencieusement les probabilités du modèle actif dans le classement.

Le classement et l’affichage des phases de puits utilisent aussi SC+SN du modèle partagé. Les anciennes fourchettes fixes 60–70 %, 30–45 %, 20–30 % ne passent plus devant ces résultats. Les préférences de travail selon le puits sont conservées, avec repli sur les actions légales lorsque la phase préférée n’en fournit aucune. Le niveau connu de l’objet et la calibration du contexte sont repris dans l’explication ; la même observation n’est pas calibrée une deuxième fois.

## Puits

- SC : gain nominal, aucune perte, puits conservé, même au-delà de 100.
- SN/EC : comptabilité `max(0 ; puits avant + poids perdu − poids tenté)`.
- **Suppression du plafonnement artificiel à 100** dans les pertes simulées.
- Exemple vérifié : puits 180, EC sur une rune de poids 1 sans perte de caractéristique → puits 179. Un SC avec puits 180 le laisse à 180.
- Un over reste une caractéristique, pas du puits déjà acquis. Pas de récompense d’entraînement pour fabriquer artificiellement une réserve.

Les bornes techniques d’entrée, comme 30 000, sont des limites de validation du logiciel, pas des limites annoncées du jeu.

## Gardes communes et malus

Le moteur applique les mêmes gardes conservatrices que le conseiller : poids total d’une ligne en over ≤ 101, exos positifs cumulés ≤ 101 ; une ligne naturellement plus lourde reste autorisée dans son maximum naturel. L’ancienne limite supplémentaire cumulant les overs dans le simulateur est retirée.

**Les malus ne sont plus simulés avec une demi-densité supposée.** Le moteur et l’entraîneur refusent explicitement un profil signé non validé ; le conseiller affiche une indisponibilité claire au lieu d’inventer une pose. Cela sécurise cette limite, sans prétendre que toutes les règles de FM des malus sont désormais connues.

Les gardes de 101 restent des choix conservateurs du logiciel. L’harmonisation ne les transforme pas en règles serveur prouvées.

## Apprentissage à partir des transitions réelles

Un modèle empirique commun utilise seulement les transitions complètes qualifiées : captures écran certifiées ou événements vidéo visuellement et comptablement cohérents. Les anciennes lignes OCR non certifiées ne suffisent plus à modifier les probabilités via l’adaptateur hybride.

La correspondance exige : **même objet, même rune, même jet complet, même puits et mêmes bornes/poids naturels**. Une donnée d’un autre objet ou d’un autre état n’est pas ajoutée aux comptages exacts.

À partir de 30 observations comparables, les probabilités sont corrigées avec un a priori commun de 200 essais :

`probabilité corrigée = (200 × probabilité modèle + 100 × nombre du résultat) / (200 + nombre total)`.

La part réelle augmente avec les effectifs. Aucun second ajustement ne recompte les mêmes observations lorsqu’elles sont déjà incluses dans ces probabilités.

### Les pertes servent aussi aux essais

Pour un contexte exact ayant au moins 30 observations, et un résultat SC/SN/EC ayant au moins 5 exemples, le moteur peut rééchantillonner un état après réellement observé, conditionnellement au résultat tiré. Cette part est limitée à `n/(200+n)` ; le reste utilise la répartition de pertes provisoire du modèle.

Les pertes observées ne sont donc plus cantonnées au rapport : elles peuvent influencer les essais à une pose, les anticipations et l’entraînement. Un état simulé reste une requête au modèle ; il n’est jamais enregistré comme une nouvelle tentative réelle.

Sans contexte comparable ou avec trop peu d’exemples, le moteur conserve son repli théorique identifié. Il ne prétend pas avoir appris la loi complète des pertes du serveur à partir d’une vidéo.

## Entraîneur et audits reproductibles

L’option **Utiliser les observations réelles fiables** est activée par défaut dans l’interface. Elle ajoute les données qualifiées de l’objet à la physique des épisodes virtuels. Le mode purement théorique reste possible en décochant l’option.

Chaque entraînement utilisant cette option conserve `empirical_snapshot.json` et son empreinte. Les audits relisent cet instantané, jamais la base actuelle à sa place. La suppression ou la correction ultérieure d’une observation change le modèle suivant et sa compatibilité ; elle ne réécrit pas un ancien résultat.

Les échantillons sont ordonnés de manière canonique avant tirage : même instantané et même graine donnent les mêmes pertes, y compris après sauvegarde/rechargement. Les révisions sont calculées par objet ; une observation ajoutée sur un autre objet n’invalide pas inutilement son entraînement.

La nouvelle version exclut les anciens modèles du chargement actif sans supprimer leurs fichiers. La récompense reste le jet complet, jamais une ligne isolée ou le gain de puits. Les préparations et overs temporaires restent expérimentaux : aucun gain global n’a été établi par les essais antérieurs, réalisés avec l’ancien simulateur.

## Sélection en direct et coordination avec l’autre audit

Les corrections de l’autre conversation sont préservées : trace du classement, phases, audit du sélecteur complet, empreintes de code et de prix/réglages, invalidation et purge des anciens résultats.

L’audit du sélecteur signe aussi l’instantané empirique. Une politique auditée en simulation seule n’est pas autorisée dans un contexte réel différent. Si le sélecteur reçoit des corrections live non figées, son influence apprise est désactivée, sauf si chaque action disponible possède suffisamment de mesures exactes qualifiées et que les comptages live correspondent à l’instantané audité. Dans ce cas, les corrections par voisins ne sont pas appliquées à nouveau.

Cette règle privilégie l’absence d’influence non auditée plutôt qu’une activation trompeuse. Les rapports distinguent le gain du simulateur et une éventuelle amélioration en jeu, qui reste à mesurer.

## Limites restantes

Les coefficients provisoires et les pertes de repli ne sont pas une reconstitution certifiée du serveur. Il faut des observations comparables pour améliorer les cas concernés. Les malus restent indisponibles tant que leurs règles ne sont pas validées. Aucun taux de réussite réel égal ou supérieur à celui d’un bot tiers n’est annoncé.

La validation détaillée, les empreintes et les fichiers modifiés sont enregistrés dans le compte rendu de livraison et l’inventaire d’harmonisation.
