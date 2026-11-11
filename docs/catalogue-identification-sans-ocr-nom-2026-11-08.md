# Nom et logo de l'équipement en détection automatique

Mise à jour suivante : le cas des objets avec peu de caractéristiques, dont le
Gelano, et la remise à zéro lors d'un changement d'objet sont traités dans
`docs/correction-gelano-changement-objet-2026-11-08.md`.

Cette modification remplace le recours automatique à l'OCR du nom décrit dans
le rapport d'identification initial. Elle conserve la lecture des nombres et
des caractéristiques par OCR ; le nom provient exclusivement des associations
du catalogue local et des références visuelles déjà vérifiées.

## Cause constatée et correction

Sur les captures de 20 h 48 et 20 h 54, la petite zone utilisée par l'ancien
comparateur tronquait le logo. Le catalogue possédait pourtant déjà les noms
et les images correspondantes. La zone dédiée au nouveau comparateur inclut
le logo complet et une marge pour le placement et l'échelle de l'interface.
Le suivi temporel conserve son ancienne zone pour préserver sa compatibilité.

Le nouveau comparateur utilise les bornes naturelles pour présélectionner les
équipements, puis aligne leurs sprites transparents dans l'emplacement actuel,
à plusieurs tailles et positions. Les pixels extérieurs à la silhouette du
sprite ne participent pas à la comparaison. Il ne lit ni le nom ni l'historique
pour trouver l'identité. Trois caractéristiques concordantes au minimum, aucune
borne contradictoire, un écart RGB quadratique ≤ 24 et une marge ≥ 6 avec le
second candidat sont requis. Ces seuils sont des distances et ne sont pas une
probabilité calibrée de fiabilité.

Le parcours automatique du lecteur rapide et du lecteur complet ne lance plus
l'OCR du nom. Une ambiguïté n'est pas départagée par un nom lu dans l'historique.
L'ancienne fonction reste disponible uniquement pour les appels explicites de
diagnostic et leurs tests de compatibilité (`allow_name_ocr=True`), sans option
d'activation dans le parcours automatique.

L'association catalogue autorise plusieurs objets pour une même icône. Les
bornes et la catégorie indépendante, lorsqu'elle est connue, servent à les
départager. Si elles ne suffisent pas, l'identité reste inconnue. Les objets
ayant trop peu de caractéristiques lisibles ou un visuel absent/inexploitable
ne sont pas annoncés comme reconnus.

Après trois captures cohérentes, le nom officiel vérifié alimente la carte
d'équipement existante ; elle charge l'image officielle par son identifiant
d'icône. Ce nom reste affichable indépendamment de la complétude du jet actuel.

Le stockage historique « une icône = un nom » ne doit pas bloquer un objet du
catalogue départagé par ses bornes. Les identités officielles n'y sont donc plus
réinscrites. Une ancienne association locale différente ne peut plus opposer
un veto à une identification officielle du logo actuel.

## Vérifications effectuées

Les deux captures complètes ont été passées dans la normalisation d'atelier et
le vrai `ItemIdentityReader`, avec la fonction de lecture du nom remplacée par
une erreur et le catalogue de noms enregistrés rendu inaccessible au lecteur :

| Capture | Identité retournée | Premier passage | Passage en cache |
|---|---|---:|---:|
| 20 h 54 min 41 s | Anneau du rat brâkmarien | 8 260,52 ms | 15,62 ms |
| 20 h 48 min 31 s | Anneau du Cycloïde | 1 243,24 ms | 22,26 ms |

Le premier passage de la première capture inclut la construction froide de
l'index. Les nombres de caractéristiques sont réellement lus par le backend
OCR. Aucun OCR de nom n'a été appelé. Ces deux captures ne démontrent pas une
précision universelle pour tous les équipements et toutes les échelles du jeu.

Tests : `Tests/test_slot_catalogue_identity.py` et ses deux petites fixtures
de logos issues des captures fournies. Ils couvrent les deux identités réelles,
les bornes incompatibles, le logo vide, l'interdiction de l'OCR du nom même pour
un inconnu, un logo partagé entre deux objets, le filtrage par catégorie,
l'affichage du nom et de l'icône, le stockage historique en collision et son
ancien nom erroné. La revue a reproduit ce dernier cas avant sa correction.

Les anciens tests du cache OCR de nom l'activent désormais explicitement : ils
ne représentent plus le comportement automatique par défaut. Le groupe ciblé
de 40 tests passe. Le dernier journal complet est
`.test-tmp/catalogue-slot-pytest-final.log`.

Dernier passage complet, après correction du veto historique : **1 784 tests
réussis, 26 ignorés, 42 sous-tests réussis**, sans échec, en 126,26 s. Les trois
tests du chemin OCR de diagnostic conservé ont ensuite été rendus explicitement
compatibles avec l'option de diagnostic ; leur groupe de 16 tests passe également.
Le manifeste de cette livraison est
`docs/catalogue-identification-sources-2026-11-08.json`.

Les tests du correctif précédent des zéros ont également passé la suite
complète : 1 775 tests réussis, 26 ignorés et 42 sous-tests réussis.

## Application

Fermer le processus Forgely déjà ouvert, puis relancer `OUVRIR FORGELY.bat`.
Le changement concerne les sources locales ; aucun binaire n'a été reconstruit,
aucune modification n'a été publiée sur GitHub. Le dossier n'a toujours pas
de métadonnées Git permettant un commit local.
