# Reprise Forgely — diagnostic OCR du 10 novembre 2026

Conversation d'origine : `6af34cb5-7f68-83ed-8da9-2747a05ed0bd`,
« Correction Forgely performances OCR ». Conversation récupérée via read_thread.
Le message de diagnostic enregistré est lui-même tronqué après « JET PARTIEL
STABILISÉ » ; aucune capture jointe n'y est disponible.

## Contraintes à conserver dans Work

- Préserver l'Anneau du Cycloïde choisi et ses objectifs tant qu'un changement
  d'objet n'est pas confirmé. Une icône illisible n'établit pas ce changement.
- Distinguer l'identité conservée, les anciennes valeurs affichées, et les
  mesures actuelles suffisamment confirmées pour autoriser un conseil.
- Ne jamais compléter une valeur illisible, un puits ou un résultat SC/SN/EC
  par une supposition. Une variation signée ne prouve pas un résultat de rune.

## Diagnostic et changements

1. `Application/forgely_fast_preview.py` : l'absence d'icône ou de structure
   atelier suspend la lecture sans effacer la référence visuelle. Les suivis
   temporels sont vidés à la suspension : aucun événement ne traverse le trou
   de visibilité. Trois captures traitées consécutives d'une même nouvelle
   icône sont nécessaires pour remplacer la référence. Un changement de compte
   conserve la réinitialisation complète. L'historique textuel de secours est
   mis en cache sur pixels exactement identiques, avec une expiration de 2 s ;
   les pixels modifiés déclenchent immédiatement l'OCR. Ce composant reste
   provisoire et n'écrit ni observations ni apprentissage.
2. `Application/forgely_workshop_readings.py` : l'affichage fusionne les dernières
   valeurs confirmées avec les lignes partielles récemment stabilisées. Une
   lecture `Tacle: 0` ne masque plus le reste de l'ancien jet. Les états par ligne
   continuent de distinguer les données anciennes ; snapshot() reste nécessaire
   pour tout conseil. Aucune valeur manquante n'est inventée.
3. `Application/forgely_zone_cache.py` et `Application/forgely.py` : la zone
   `current_jet` rejoint les zones numériques confirmées. Leur provenance est
   transmise aussi lors de la publication anticipée des nombres. Réutilisation
   uniquement sur pixels identiques. L'identité vérifiée utilise désormais une
   variable distincte pour ne plus écraser la lecture atelier réutilisée.
4. `Application/forgely.py` : avant d'accepter jet/puits, comparer la signature
   exacte des zones atelier de la capture traitée à la dernière capture publiée.
   Si elles diffèrent, rejeter les nombres, invalider leur autorisation de conseil
   et demander une nouvelle confirmation. Les événements historiques persistants
   ne sont pas supprimés par ce filtre numérique.
5. Zones OCR : vérification des lecteurs existants, de l'isolation des colonnes,
   des valeurs courantes et des captures réelles disponibles. Pas de déplacement
   arbitraire des coordonnées sans capture du défaut terrain. Le lecteur actuel
   sépare jet, modifications, historique, rune et reliquat ; son cache utilisait
   encore seulement le nom de zone de l'ancien lecteur.

## Validation exécutée

- Six nouvelles régressions dans `Tests/test_diagnostic_continuity.py` : absence
  temporaire d'icône, remplacement confirmé, jet partiel, cache historique,
  cache du jet courant et rejet numérique après modification des pixels.
- Les défauts ont été reproduits avant correction (tests en échec).
- Tests historiques adaptés pour faire changer les pixels quand le faux OCR
  change de texte, et attendre une seule lecture des pixels inchangés.
- Suite ciblée continuité/identité/puits/historique/pipeline : **157 réussites**.
- Suite zones/valeurs courantes/calibration/historique/captures : **200 réussites**.
- Contrôle final après séparation des variables de cache et identité :
  **30 réussites**. Ces ensembles se recouvrent ; ne pas additionner les totaux.
- Premier essai : deux erreurs de création du dossier temporaire système,
  résolues en utilisant `--basetemp .test-tmp/diagnostic-20261110-b`.

## Limites et prochaine vérification

Les sources et captures de test locales sont accessibles ; le dossier n'a pas
de métadonnées Git exploitables. Aucun commit, envoi distant ou reconstruction
d'exécutable n'a été réalisé. Lancer les sources avec le lanceur habituel.

La fenêtre DOFUS du diagnostic n'a pas été observée en direct pendant cette
correction. Les mesures terrain (cycle médian 4,1 s, 24 pertes d'icône, OCR ancien)
ne sont donc pas remplacées par une promesse de délai inférieur à une seconde.
Les tests valident la réduction des appels inutiles et le rejet des nombres
obsolètes, pas un nouveau p95 en jeu. Une animation persistante peut retarder la
confirmation car le filtre de fraîcheur est volontairement exact et conservateur.

Pour poursuivre : lancer les sources, reproduire sur le Cycloïde, exporter le
diagnostic et les zones atelier si l'icône ou les chiffres restent illisibles.
Comparer les pertes/réinitialisations, les rejets, les durées capture-vers-affichage
et les pixels des zones avant toute nouvelle correction de géométrie. Conserver
les anciennes valeurs comme anciennes, jamais comme mesures actuelles.

## Second diagnostic terrain et correction du filtre de fraîcheur

Le diagnostic suivant confirme l'Anneau du Cycloïde et les onze lignes OCR,
avec un reliquat OCR dédié de 2.0, mais sans stabilisation. Le cycle médian
terrain est passé de 4103 à 2436 ms ; la lecture rapide médiane est de 47 ms,
mais le délai capture-vers-affichage médian reste de 1672 ms. Ces mesures
proviennent du diagnostic utilisateur, et non d'un nouveau benchmark local.

Cause confirmée dans le code : le filtre ajouté lors de la première correction
comparait toute la signature atelier. Un changement de l'historique, de la
sélection de rune ou de la colonne Modif. pouvait donc invalider des chiffres
strictement inchangés et recommencer leurs confirmations. Cette portée était
trop large.

Le contrôle des résultats numériques utilise désormais une provenance distincte
dans `ConfirmedAtelierRead` : pixels exacts du jet courant, du reliquat dédié et
du logement objet, dimensions et contexte de fenêtre. Les autres zones continuent
de déclencher leur propre lecture sans remettre automatiquement à zéro les
confirmations numériques. La réutilisation d'un atelier entier conserve son
contrôle intégral ; elle ne réutilise donc pas un ancien historique.

Le diagnostic affiche aussi le nombre de rejets numériques, les compteurs de
confirmation jet/puits et le motif d'attente. Cela permettra de distinguer un
changement réel des pixels numériques d'une autre cause de non-stabilisation.

Clarification demandée par l'utilisateur : Agilité 20, Initiative 195 et Tacle 0
doivent suivre la même vérification automatique que toutes les autres lignes.
Le minimum naturel n'est pas un seuil de validité d'une mesure après FM.
Aucune confirmation manuelle supplémentaire n'est exigée pour ces valeurs ;
aucune valeur n'est ramenée artificiellement au minimum du catalogue.

`Tests/test_numeric_freshness_scope.py` vérifie les zones indépendantes, le rejet
des chiffres/puits/icône modifiés et le contexte de fenêtre. Son test d'intégration
fait passer le jet exact du second diagnostic, y compris ses valeurs sous les
minima, à travers trois messages issus de captures distinctes avec un historique
qui change. La stabilisation est vérifiée avec des puits de 0, 2 et 2.9.
Ce sont des tests locaux contrôlés, pas une validation visuelle des chiffres
effectivement présents dans la fenêtre DOFUS de l'utilisateur.

Validation finale de cette seconde correction : **351 tests réussis**, en
62.21 s, plus compilation Python réussie. Un avertissement de destruction d'une
variable Tkinter hors du thread principal a été émis en fin de vie d'un objet
de test ; aucun test n'a échoué. Dossier temporaire de cette exécution :
`.test-tmp/diagnostic-followup-final`. La stabilisation dans la session DOFUS
réelle reste à vérifier après redémarrage des sources corrigées.

## Transmission anticipée des nombres — suite de l'audit des contradictions

Demande utilisateur : effectuer les corrections nécessaires après avoir identifié
l'attente commune des zones OCR et le diagnostic incohérent sur les runes.

- `read_atelier(..., five_zones=True)` transmet maintenant un résultat numérique
  dès la fin des lecteurs jet/reliquat via `on_numeric`, sans attendre les tâches
  historique et Modif. Un test bloque volontairement ces deux tâches et vérifie
  que les nombres sont transmis pendant ce blocage. Un autre exerce directement
  `Forgely.observer_worker`, pas seulement le lecteur de zones.
- La transmission anticipée garde l'identité vérifiée du logement courant, la
  protection contre les infobulles et le contrôle de fraîcheur des pixels. Aucun
  puits absent ni jet vide n'est complété. Les messages sont toujours liés à la
  génération et à la fenêtre de capture.
- Une lecture numérique anticipée porte `complete=False`. Elle ne peut donc pas
  être réutilisée comme un atelier complet avec un historique vide. La fin de
  lecture enrichit seulement les nombres déjà confirmés et ne compte jamais
  comme une nouvelle capture de confirmation.
- Le diagnostic distingue une zone rune volontairement non demandée d'un OCR
  effectivement illisible. L'absence de preuve SC/SN/EC reste signalée : elle
  n'est pas transformée en un résultat supposé.
- Nouvelles mesures : `capture_vers_publication_numerique`,
  `capture_vers_affichage_numerique` et retard de la dernière lecture numérique.
  Le retard de l'observation complète reste mesuré indépendamment.
- Vérification du partage existant : le backend OCR mutualise déjà les requêtes
  identiques en cours et les résultats récents entre lecteurs. Ses tests ont été
  inclus ; aucun second cache global de groupes historiques n'a été ajouté.

Validation élargie : **369 tests réussis, 1 ignoré**, 36.54 s ; compilation des
quatre modules modifiés réussie. Les cinq régressions de cette étape sont dans
`Tests/test_numeric_delivery_latency.py`. Aucun échec de test.

Limite : le cycle de l'observateur attend encore la fin de l'historique avant
son itération suivante. Cette correction retire cette attente de la transmission
du jet/puits de la capture déjà traitée ; elle ne supprime pas le travail utile
de suivi des événements. Les tests contrôlent l'ordre des publications et les
protections, pas un nouveau p95 réel dans DOFUS. Le diagnostic terrain doit
être repris après redémarrage avec `OUVRIR FORGELY.bat`, dont le lancement des
sources locales a été vérifié.

Contrôle isolé supplémentaire des objectifs mesurés et de leur interface :
`Tests/test_measured_goals.py`, **14 réussites, aucune exclusion** (1.59 s).

## Amulette Tétriste et généralisation à tous les profils

L'utilisateur a fourni la capture du 10 novembre à 18:35:02 puis demandé que
le blocage ne dépende d'aucun objet/jet. Le diagnostic complémentaire indique
**15 lectures numériques rejetées pour 15 lectures terminées**, confirmations
(0,0), alors que les cinq caractéristiques sont lues et le reliquat vaut 0.0.
Il confirme donc un veto de fraîcheur, pas un rejet des nombres négatifs.
L'ancienne ligne « source modifiée » ne distinguait pas les composantes du veto ;
elle ne permet pas d'attribuer les quinze rejets à un pixel précis de la session.

Modifications communes à tous les objets :

- Provenance numérique convertie dans un mode RGB commun. En cas de différence
  des pixels bruts, comparaison des traits de premier plan du jet et du reliquat
  sur leur fond de ligne, sans redimensionnement/lissage ni tolérance au nombre
  de traits modifiés. Les signes et points décimaux restent dans la comparaison.
  Les variations faibles du fond ne remettent plus les compteurs à zéro.
- L'icône utilise la même distance visuelle (17) que le suivi indépendant de
  l'objet, au lieu d'exiger des ombrages identiques au pixel près pour confirmer
  les nombres. Fenêtre, dimensions et provenance restent obligatoires.
- Le diagnostic distingue les motifs `jet`, `reliquat`, `icone`, `dimensions`,
  `contexte_fenetre`, `provenance_absente` et `capture_absente`.
- Détection structurelle de l'atelier indépendante du vert : les sondes de
  géométrie, couleur de panneaux et titre restent requises, puis les glyphes
  lumineux de la colonne actuelle peuvent être rouges, blancs ou verts. Un
  jet exclusivement négatif/neutre n'exclut donc plus l'atelier.
- Le diagnostic utilise le même référentiel complet que le lecteur actuel.
  La Portée de la Tétriste n'est plus faussement présentée comme un exo du fait
  d'un ancien CSV partiel. Les fichiers de référence explicitement passés aux
  outils/tests restent respectés.
- L'affichage flottant indique « Lecture à confirmer » et son rapport montre
  le motif réel de l'attente. Le type interne historique `calcul` reste compatible,
  mais ne prétend plus qu'un calcul tourne quand des mesures manquent.

Validation :

- La capture fournie est effectivement lue par Tesseract local : Portée 1,
  Force/Intelligence/Chance/Agilité -15, reliquat 0.0. Son atelier normalisé et
  isolé a été enregistré dans `Tests/fixtures/workshop_tetriste_20261110.png`.
- Test de livraison jusqu'à l'interface sur trois captures distinctes, avec
  variation de fond et de format RGB/RGBA : le jet et le puits se stabilisent.
- Test commun de **2 725 profils avec caractéristiques** du catalogue, chacun
  aux minima, maxima, à zéro et sous les minima. Les valeurs synthétiques de ces
  tests ne deviennent jamais des données observées dans l'application.
- Détection vérifiée sans vert, conservation des signes, rejet d'un vrai
  changement de traits, protections d'identité et historique conservées.
- Suite élargie : **410 réussites et 6 sous-tests réussis**, 39.48 s.
- Après ajustement final du rapport d'attente : **42 réussites**, 9.47 s,
  et compilation des six modules modifiés réussie.
- Les tests utilisant `tempfile` ont d'abord rencontré les restrictions du
  dossier temporaire système. Relance réussie avec TEMP/TMP et basetemp dans
  `.test-tmp`, sans changer les exigences des tests.

Limite : ces régressions et la capture démontrent les cas traités, pas l'absence
absolue de tout défaut sur une session future. Une valeur réellement illisible,
une icône inaccessible ou un changement effectif doivent toujours suspendre
le conseil et indiquer pourquoi. Ne jamais contourner ces cas en inventant
une valeur ou en autorisant un ancien jet. Redémarrer les sources corrigées
pour confirmer le résultat dans la session native DOFUS.

## Conseil suspendu malgré la stabilisation : limitation distincte du modèle

Le diagnostic terrain suivant confirme huit lectures concordantes du jet et du
puits, avec une dernière lecture numérique affichée en 674 ms. L'utilisateur
signale néanmoins « Conseil suspendu ».

Reproduction directe du moteur sur le jet de la Tétriste, avec objectifs de
remonter les caractéristiques négatives à zéro : `advise` renvoie `rune=None`,
`kind='bloqué'`, `summary='Profil avec malus non validé'`. Dans
`forgely_decision.py`, un veto explicite rejette les valeurs courantes négatives
ou les bornes naturelles négatives après le contrôle d'objectif déjà atteint.
Ce n'est donc pas, dans ce cas reproduit, un défaut de stabilisation ou une
absence de résultat SC/SN/EC dans l'historique.

Correction de communication et d'affichage :

- Les tests sur les 2 725 profils concernent **la lecture/stabilisation**, pas
  la disponibilité d'un modèle de conseil pour chacun. Le précédent bilan
  ne doit pas être interprété comme la prise en charge de tous les malus.
- Le titre de l'interface affiche maintenant la raison exacte renvoyée par
  le moteur, au lieu de « Conseil suspendu » pour tous les refus.
- Le rapport compact et le diagnostic affichent également l'explication du
  refus. Le diagnostic inclut `CONSEIL` et `MOTIF CONSEIL` à partir du résultat
  courant du moteur, indépendamment de la santé des lectures.
- Le veto des règles signées non validées reste actif. Il n'a pas été supprimé
  pour produire une rune dont les contraintes, pertes ou probabilités ne sont
  pas modélisées correctement. Implémenter et valider ces règles reste un
  travail distinct nécessaire pour conseiller la remontée des malus.

Validation : reproduction avant correction dans
`Tests/test_signed_advice_explanation.py`, puis **47 tests réussis** (12.99 s),
comprenant la cohérence des refus malus, l'objectif déjà atteint, les lectures
universelles, la continuité et les masquages. Compilation des trois modules
modifiés réussie. L'affichage est corrigé ; **le moteur de conseil avec malus
reste non pris en charge**.

## Infobulle tronquée puis reprise confirmée

Le diagnostic utilisateur suivant reproduit une infobulle dans les effets :
`POIDS 5`, `PRIX MO`, plusieurs `QUANTIT`, description d'objet mélangée aux cinq
caractéristiques. L'ancien détecteur attendait les expressions entières ou
`poids 10` : son compteur restait donc à zéro sur ce texte contaminé.

Correction dans `effects_text_occluded` : normalisation des accents et détection
des préfixes de métadonnées prix/quantité ainsi que du poids numérique, quel
que soit son montant. Le callback numérique et le parcours complet utilisent
la même fonction. Une capture ainsi reconnue ne publie aucun nombre, invalide
les entrées `effects` **et `current_jet`**, y compris leur cache confirmé, et
affiche un motif de masquage invitant à éloigner le pointeur. Le texte contaminé
reste disponible au diagnostic, jamais comme jet actuel utilisable.

Onze nouvelles régressions dans `Tests/test_truncated_tooltip.py` : texte exact
fourni, variantes tronquées, effets normaux non masqués, refus de publication
anticipée et éviction du cache de la zone courante. Validation élargie :
**92 tests et 3 sous-tests réussis**, 18.08 s ; compilation des deux modules
modifiés réussie.

Pendant cette correction, un nouveau diagnostic terrain montre dix
confirmations jet/puits, une infobulle comptée/écartée, et une dernière lecture
numérique affichée en 611 ms. Il confirme à nouveau un jet lu et un puits 0.0
confirmé. Le refus courant est explicitement « Profil avec malus non validé ».
Les médianes restent distinctes : cycle complet 1090.6 ms, affichage numérique
1054.8 ms. Ni la dernière lecture à 611 ms ni ces tests n'établissent un délai
toujours inférieur à une seconde. La prise en charge du conseil signé/malus
reste à implémenter/valider ; elle n'est pas débloquée par les corrections OCR.

## Conseils signés demandés, simulateur automatique maintenu désactivé

L'utilisateur demande la prise en charge de tous les profils avec malus et
rappelle que le simulateur a été retiré des conseils automatiques. Cette
préférence est conservée : aucun worker de simulation n'est lancé par le
conseil signé. L'entraîneur et le simulateur manuel ne sont pas réactivés.

Implémentation : le conseiller ne rejette plus un objet entier ni une ligne
à améliorer uniquement parce qu'une valeur/bornes/cible est négative. Il
compare les gains nominaux des runes vers les cibles signées ; une remontée
encore négative est identifiée comme `reduction_malus`. Une petite rune peut
finir une cible entre deux paliers sans attribuer son gain nominal à l'OCR.
Les lectures incomplètes et le reliquat inconnu restent bloquants. Les plafonds
positifs connus restent contrôlés même sur une ligne naturelle négative.
Les contraintes spécifiques non vérifiables restent signalées, jamais certifiées.

Pour tous ces profils, les probabilités et distributions de pertes ne sont pas
extrapolées : prediction=None, aucun relevé simulé réutilisé, débit SN/EC du
puits indiqué inconnu. Le classement est nominal et explicable, pas un modèle
serveur validé. La suppression d'un malus n'est jamais du puits déjà acquis.
Le calcul et l'audit des transferts SN/EC signés exigent le reliquat lu plutôt
qu'une application abusive des poids positifs. Les données réellement capturées
restent enregistrables sans être arbitrairement qualifiées de calibration fiable.

Validation : **154 tests réussis**, 7.32 s, dont les conseils sur **630 profils
du catalogue avec malus et runes connues**, les objectifs négatifs et nuls,
le parcours réel du copilote pour la Tétriste, l'absence d'appel au simulateur,
les protections OCR et la non-régression des conseils positifs. Les anciens
tests de refus général du conseiller ont été remplacés par des tests de
recommandation nominale ; le refus du simulateur signé non validé reste testé.

Recherche demandée sur les pertes : voir
`docs/MALUS_REGLES_SOURCES_2026-11-10.md`. Règle communautaire du coût de pose à
demi-poids et exception -1 → 0 trouvées ; distribution des pertes sur toutes
les lignes signées et tous les franchissements non établie. Base native lue
sans modification : 71 transitions, aucune avec malus, donc pas de calibration
Tétriste disponible. Ne pas annoncer que le modèle signé est intégralement validé.

Dernière demande utilisateur : il propose d'enregistrer une session de la
Tétriste. Réponse donnée : oui, analyser jet/puits/rune/historique avant-après,
avec pauses pour séparer les poses, et conserver une preuve vidéo par règle
déduite. Les passages -2→-1 et -1→0 sont utiles. Ne pas extrapoler les cas non
observés, les probabilités exactes ou tous les profils à partir d'une seule vidéo.

Relecture du code signée : une comparaison de paliers pouvait encore afficher
les probabilités positives lorsque seule la cible était négative. Défaut reproduit
par un test, corrigé dans `tier_comparison`. Contrôle final : **155 tests réussis**,
9.65 s, puis compilation réussie des modules modifiés. Le simulateur automatique
reste exclu du conseil.

Vidéo reçue pour analyse : `Enregistrement de l'écran 2026-11-10 191542.mp4`,
67.2 secondes, 30 images/s, 2016 images, 1918 × 1078. Dossier d'analyse local :
`work/session_malus_20261110`. La première image montre déjà Force +1 sur la
Tétriste : cela interdit de présenter une ancienne règle « malus jamais positif »
comme une impossibilité certaine de la version PC actuelle. L'identité est
corroborée par l'icône et le profil visibles ; l'enregistrement démarre après
des poses antérieures, donc la formation de cet état initial n'est pas observée.

Analyse vidéo poursuivie : 135 images à pas de 0.5 s, seize transitions
contrôlées visuellement. Annotations et empreinte du fichier dans
`work/session_malus_20261110/verified_transitions.json`, sans import dans les
observations réelles. Rapport dans
`docs/ANALYSE_SESSION_TETRISTE_2026-11-10.md`.

Faits importants : coût Pa Cha restant négatif de 1.5, coût Ra Age -15→-5 de
5 directement en puits, pertes négatives cohérentes avec 0.5/point sur les
caractéristiques primaires. Pa Cha Chance -3→0 accompagnée de Force -9→-15
avec puits constant 36.5 : cohérent avec coût de pose de 3 pour cette arrivée
à zéro. Ensuite Chance 0→-3 sur une Pa Age sans gain avec puits toujours 36.5 :
le puits ne protège pas automatiquement les malus déjà remontés. Des Ra Cha et
Ra Age sur -5 affichent seulement +5 jusqu'à zéro lors de réussites sans perte ;
elles ne mesurent pas le coût SN/EC de ces franchissements.

L'utilisateur a ensuite proposé une méthode « faire sauter le PO, obtenir 51,
corriger les quatre malus pour au maximum 30, repasser PO en dernier » et
demandé une analyse. Points à corriger : poids perdu différent du puits net
(coût de pose à déduire), budget 30 non garanti (échecs et exception à zéro),
malus améliorés dégradables avant consommation du puits, repassage PO SN/EC
susceptible de détruire les zéros et sans création automatique de nouveau puits.
La vidéo garde PO 1 et ne filme ni sa chute ni son repassage final. Ne pas
annoncer que cette séquence est validée par la vidéo.

## Complément vidéos 193444 et 193651
Analyse conservée dans docs/ANALYSE_SESSIONS_TETRISTE_193444_193651.md. Le deuxième clip conserve PO zéro. Le troisième filme deux repassages sans perte, une chute PO sur Ra Cha échouée (puits 2→43 = 2+51-10), et deux passages Intelligence -4→+6 sur Ra Ine. Le second consomme directement 10 de puits, sans autre perte. Ne plus interpréter les gains +5 précédents comme un plafond universel à zéro. Charge entière de rune au franchissement positif dans ces observations ; ne pas généraliser la formule à toutes les stats. Preuves et empreinte conservées dans work/session_malus_20261110_193651. Aucune règle moteur ni base de jeu modifiée pour cette analyse.

## Correction intégrée après demande de régler les problèmes
forgely_pool_ledger : calcul signé partagé et borné aux quatre stats de base, charge moitié si destination nominale strictement négative, entière sinon ; pertes pondérées selon signe ; gains ciblés partiels restent ambigus. Audit expert utilise ce même calcul et détecte les contradictions. Conseil expose attempted_weight et exposition correspondante, sans simulation ni taux inventés. Pas de calcul sans puits initial connu ni sur transition incomplète. Tests/test_signed_video_rules.py ajouté ; ancienne attente de refus systématique corrigée. Validation finale : 136 tests passent (5,58 s), py_compile réussi. Pas de vérification live DOFUS ou de reconstruction d'exécutable.

## Médaille Kido : PA manquant malgré Wi1PA explicite
Cause reproduite : la frontière de mot du parseur rejetait le nombre collé au glyphe OCR Wi. Correction bornée aux lignes entières Wi + nombre explicite signé + PA/PM ; pas de valeur inférée, zéro et signe conservés, noms/descriptions non réparés. Tests/test_compact_pa_ocr.py : diagnostic Kido complet stabilise jet et puits 0,2 après trois lectures, contradictions et absences restent refusées. Validation : 61 tests passent, compilation réussie. Les latences 1–4 s du diagnostic ne sont pas résolues par cette correction de parsing. Session ouverte non redémarrée.

## Capture Kido 211418 : zéro PA blanc et reliquat tronqué
Capture utilisateur conservée en Tests/fixtures/kido_zero_pa_20261110.png. Reproduction réelle : lecteur current_jet rejetait # OPA ; read_current_jet_ocr omettait la récupération des zéros blancs déjà présente dans l'ancien chemin. Raccordée uniquement si token OPA/OPM ambigu et stat absente. La détection par bandes violettes ratait la ligne bordée en rouge : ajout de détection des lignes de texte neutre, sans position ni profil d'objet imposés. Profil de formes exactes white_zero_pa_kido_20261110 annoté visuellement (0 et libellé PA), provenance et empreinte conservées. Ce profil est une calibration, pas une validation indépendante ; tests de glyphe/libellé altérés refusés. OPA brut reste ambigu. Deuxième défaut reproduit : crop reliquat commençait trop à droite (iquat : 94), borne gauche passée de .325 à .315. Lecture réelle de la capture après correction : 7 stats dont PA0, puits94. Tests : 227 passent après correction zéro ; après ajustement reliquat, 84 tests ciblés passent, compilation réussie. Totaux se recouvrent. Latence globale et rejets jet en session non validés ; capture statique seulement. Aucun redémarrage de l'application en cours.

## Diagnostic collé après correction zéro : reproduction du vrai chemin de capture
Nouveau diagnostic : 38 lectures, PA absent (# OPA), puits94 lisible, 14 rejets jet, confirmations0. Reproduction trouvée : Capture._focus_workshop appelle WorkshopLocator.normalize puis focus_workshop ; la précédente validation utilisait la capture brute et ne couvrait pas ce rééchantillonnage. Transform de la capture 211418 : (1.2575079872204473,-74.65303514377018,-23.478594249201308). Ajout profil exact white_zero_pa_normalized_20261110 (0 et libellé PA annotés depuis la capture connue), provenance documentée. Autre rejet : proportion blanc/clair102/176 <60% en raison de l'icône colorée. La reconnaissance exacte chiffre+libellé est maintenant vérifiée avant cette heuristique de couleur ; les formes inconnues restent refusées. Nouveau test de régression traverse normalize→focus→crop→OCR→stabilisation 3 observations et obtient PA0/puits94 avec snapshot complet. C'est une relecture de calibration, pas une validation live ni une précision indépendante. Ne pas affirmer que tous les rejets jet et la latence globale sont résolus.

## Test A/B demandé : lecture numérique isolée
Prototype hors production work/benchmark_numeric_split.py, résultats work/benchmark_numeric_split_results.json. 5 comparaisons par objet, Kido et Tétriste, vraies images normalisées et vrai OCR, caches OCR/historique froids, ordre alterné. Chemin actuel read_atelier five_zones avec HistoryReader.latest_text et livraison numérique anticipée comparé au même couple de lecteurs jet/puits seuls (2 threads). Médianes numériques : Kido1228,08ms→880,91ms (-28,3%), Tétriste731,80→699,59ms (-4,4%). Durée totale du passage actuel3061,87/1684,09ms versus numérique seul880,92/699,60ms. Jet, puits et rune/type/résumé du conseil identiques dans les10 comparaisons ; source et contexte gardés dans le prototype. Limites : captures fixes, caches froids, capture/GUI/autres workers et charge d'un historique toujours actif exclus du prototype ; pas de taux de conseil erroné ni de latence live démontrés. Aucun changement du pipeline de production pour ce test.
