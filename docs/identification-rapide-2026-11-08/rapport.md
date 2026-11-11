# Identification rapide des équipements Forgely — 8 novembre 2026

**Mise à jour ultérieure :** le parcours automatique ne lit désormais plus le
nom par OCR, même en cas d'ambiguïté. Le cadrage complet des logos permet de
reconnaître les deux nouvelles captures de 20 h 48 et 20 h 54. Voir le rapport
`docs/catalogue-identification-sans-ocr-nom-2026-11-08.md`. Le présent document
et son manifeste décrivent la livraison initiale et ses mesures, avant ce correctif.

Les sources locales ont été modifiées. L'index combine les images officielles,
la catégorie lorsqu'elle est fournie indépendamment et les bornes naturelles
observées. Le nom est relu seulement lorsque l'identification visuelle ne suffit
pas. Cela ne constitue pas une validation générale de la reconnaissance en jeu :
le diagnostic sur les trois captures existantes s'abstient sur chaque capture.

## Accès et périmètre

- Le dépôt privé `lafleche1/Forgely` est accessible par le connecteur GitHub :
  métadonnées et droits de lecture/écriture confirmés, branche par défaut `main`.
- Le dossier de travail local ne contient pas de métadonnées Git ; `git status`
  retourne « not a git repository ». Aucun commit, push ou changement distant
  n'a été effectué. L'accès technique au dépôt ne prouve pas que cette copie
  locale correspond à son état courant. Aucun autre travail local n'a été écrasé.
- Les deux catalogues CSV comptent 21 622 entrées chacun, tous types d'objets
  confondus. L'audit et l'index d'identification portent sur les 2 861 équipements
  des catégories déjà prises en charge par `EquipmentCatalog` : coiffe, cape,
  anneau, amulette, ceinture, bottes et armes.
- Le résultat n'est pas un décompte de tous les équipements, cosmétiques,
  boucliers, familiers, ressources ou runes du jeu actuel. Aucune mise à jour
  du catalogue auprès du client DOFUS ou d'un service externe n'a été réalisée.

## Audit mesuré des fichiers disponibles

`audit.json` contient les empreintes de chaque fichier, les listes de groupes,
les paires de proximité et les éventuelles ressources manquantes.

| Mesure | Résultat |
|---|---:|
| Identifiants d'icônes attendus dans le périmètre | 2 695 |
| Fichiers PNG trouvés et décodables | 2 695 |
| Fichiers attendus manquants / illisibles | 0 / 0 |
| Groupes de fichiers identiques SHA-256 | 2 |
| Groupes de pixels RGBA identiques, dimensions conservées | 2 |
| Groupes d'objets partageant exactement les mêmes pixels | 112 |
| Objets appartenant à ces groupes | 280 |
| Paires d'objets dans ces groupes | 298 |
| Paires de fichiers avec distance pHash ≤ 6 | 347 |
| Parmi celles-ci, paires avec pixels différents | 345 |

Les deux groupes de fichiers identiques sont `11027.png` / `11028.png` et
`17054.png` / `17056.png`. La différence entre groupes de fichiers et groupes
d'objets vient notamment des objets réutilisant le même identifiant d'icône.
Les 345 paires proches ne sont pas présentées comme des doublons avérés : un
pHash mesure une proximité structurelle, peut ignorer la couleur et produit
des faux positifs. Il n'est jamais utilisé seul pour attribuer un nom.

Une référence d'emplacement vérifiée, `anneau_du_cycloide.png`, est auditée
séparément ; aucun rapprochement artificiel avec les icônes de runes ou de l'UI.

Empreinte du manifeste des icônes :
`6e981e93d143314414c098ec64c504dbaa2dad77c14eb41dfe28cb279d0bdc9c`.

Empreinte du catalogue de noms :
`4377900b7c90028d0af0a10607ff14e8e87c7448e62cc652a14d63f259ed0326`.

## Fonctionnement et seuils

1. Une géométrie d'atelier validée et une icône non uniforme sont requises.
2. L'index contient 2 854 références utilisables. Sept objets sont exclus de
   l'identification visuelle car leur image est trop uniforme ; les fichiers
   restent présents et décodables, donc ne sont pas des fichiers corrompus.
3. Présélection pHash DCT 64 bits, distance de Hamming ≤ 8. Le seuil d'audit ≤ 6
   est distinct du seuil de reconnaissance. Transparence composée sur fond
   fixe `#38394e`, puis normalisation en 32 × 32 pixels pour la reconnaissance.
4. Distance RGB moyenne ≤ 10/255, marge ≥ 8 avec le second candidat compatible.
   Les concurrents jusqu'à 18 sont conservés pour calculer cette marge, même
   s'ils ne sont pas eux-mêmes acceptables au seuil de 10.
5. La catégorie est un filtre strict lorsqu'elle est connue. Le lecteur accepte
   un paramètre `category` ; le parcours automatique existant ne dispose pas
   encore d'une observation indépendante fiable de catégorie, et le laisse
   inconnu. Il ne déduit jamais cette catégorie du nom qu'il cherche à confirmer.
6. Au moins trois caractéristiques naturelles concordantes sont nécessaires
   pour attribuer automatiquement un nom sans OCR. Une borne incompatible
   suffit à rejeter le candidat. Une signature partielle ne constitue pas une
   preuve d'absence des lignes non visibles. Le jet actuel n'entre pas dans
   cette signature. Éléments, valeurs négatives et résistances en % sont distingués.
7. Une ambiguïté conserve les candidats pour le double OCR existant du nom.
   Un nom hors candidats, un candidat explicitement rejeté par ses bornes ou
   des bornes répétées contradictoires ne peuvent être réacceptés par cet OCR.
   Les homonymes restent bloqués, même si l'une de leurs images manque.
8. Sans candidat connu ni contradiction exploitable, le parcours OCR historique
   est conservé avec ses confirmations sur plusieurs captures. Une icône vide,
   un catalogue indisponible ou une lecture douteuse ne produisent pas de nom
   supposé par le nouveau moteur. Le choix manuel existant reste disponible.

Ces seuils sont conservateurs et explicites, mais ne constituent pas des
probabilités calibrées de confiance. Leur validation statistique en jeu reste
à effectuer sur des captures annotées, notamment pour les collisions d'icônes.

## Cache et intégration

- Décodage et DCT des ressources conservés en mémoire pour la durée du processus.
  Un verrou empêche les deux lecteurs de construire simultanément l'index froid.
- Cache LRU de 512 recherches, protégé entre lecteurs ; clé : empreinte exacte
  des pixels normalisés, signature naturelle complète et catégorie.
- Un résultat OCR de départage n'est pas mémorisé comme une identité universelle
  de l'icône. Les caches OCR existants continuent à dépendre des pixels.
- Les caches d'en-tête du lecteur rapide et du lecteur complet incluent aussi
  l'icône, les bornes et les candidats/vetos ; un nom inchangé ne masque plus un
  changement d'équipement ou une contradiction.
- Les ressources sont immuables pendant une session. Après remplacement des
  fichiers, redémarrer ou appeler `clear_index_cache()` ; pas de cache disque
  d'identité à risque d'être réutilisé avec un autre catalogue.
- Confirmation temporelle et rejet des captures anciennes conservés. Pas de
  simulation d'action dans le jeu, ni de données d'apprentissage réelles créées.

## Mesures et validation

Dernier passage complet : **1 762 tests réussis, 30 ignorés, 42 sous-tests
réussis**, sans échec, en 172,56 s. Les 37 tests du groupe ciblé d'identité,
d'audit et de latence passent également. Vérification de compilation Python
des sept modules/scripts modifiés ou ajoutés : réussie.

Dernier benchmark exécuté sans suite de tests ni diagnostic de captures en
parallèle, Python 3.13.17 / Windows 11 :

| Mesure | Résultat |
|---|---:|
| Construction initiale de l'index | 7 089,15 ms |
| Essais, toutes références utilisables × deux variantes | 5 708 |
| Noms corrects / abstentions / noms incorrects observés | 4 509 / 1 199 / 0 |
| Recherches, p50 / p95 / p99 | 1,96 / 2,84 / 3,48 ms |
| Recherches, maximum | 9,13 ms |
| Cache chaud, 500 répétitions, p50 / p95 / p99 | 0,65 / 0,92 / 1,04 ms |

Les deux variantes sont l'image originale et une luminosité multipliée par 1,05.
Le temps de construction varie sensiblement entre passages : 3,33 s sur un
passage précédent, 7,09 s sur le dernier. Il n'est pas masqué dans les latences
de recherche. Les seuils n'ont pas été calibrés sur les trois captures.

Les résultats finaux sont dans `benchmark-final.json`, `captures.json` et
`pytest-final.log`. Les chiffres du benchmark des références excluent le coût
de capture, l'OCR des caractéristiques, les confirmations temporelles et l'UI.
La catégorie et les bornes y sont fournies par le catalogue lui-même : il
s'agit d'un banc reproductible du moteur, pas d'une estimation de sa précision
sur des captures inconnues.

Le diagnostic réel utilise `frame_001.png`, `frame_014.png`, `frame_027.png`
des fixtures existantes, avec le vrai backend OCR et une seconde lecture
immédiate de chaque image. Les captures ne sont pas traitées comme un jeu de
vérité terrain d'identité. Aucune identité n'y a été attribuée. L'alignement des
petites icônes d'emplacement et la qualité des caractéristiques extraites restent
des limites concrètes à valider ; les seuils n'ont pas été relâchés pour forcer
une réponse sur ces trois images.

Mesures finales du lecteur complet sur ces captures, index déjà construit :
1 909,30 / 2 021,01 / 2 824,60 ms au premier passage ; 14,72 / 15,40 / 19,70 ms
au second. Deux vues OCR du nom sont demandées pour chaque premier passage ;
les répétitions peuvent encore redemander une lecture non résolue après une
seconde, alors que le backend OCR peut répondre par son propre cache. Les
compteurs JSON distinguent ces demandes des appels au backend ; ils ne sont
pas présentés comme un nombre de nouveaux processus Tesseract.

La revue indépendante a reproduit trois erreurs de sûreté (contournement d'un
veto par OCR, caractéristiques répétées contradictoires, homonyme avec image
manquante). Elles ont été corrigées après ajout de tests échouant avant les
corrections. Un cas de marge visuelle à la frontière du seuil et un cas de
résistance en pourcentage disposent également de tests de non-régression.

Le premier passage de la suite complète a échoué sur deux appels directs à
Tesseract absent du PATH et sur un test de bilan de session dont l'échec n'a
pas été reproduit dans le groupe ciblé. Ces trois tests ont ensuite réussi avec le
PATH corrigé. La suite finale utilise un dossier de données utilisateur isolé
dans le projet et le Tesseract déjà installé ; aucune dépendance n'a été installée.

## Reproduction

Depuis la racine du projet, PowerShell :

```powershell
$env:TEMP="$PWD/.test-tmp"
$env:TMP=$env:TEMP
$env:LOCALAPPDATA="$PWD/.test-tmp/identity-validation-user"
$env:PATH='C:/Program Files/Tesseract-OCR;' + $env:PATH
.venv/Scripts/python.exe -m pytest -q --tb=short
.venv/Scripts/python.exe Application/forgely_icon_audit.py --output docs/identification-rapide-2026-11-08/audit.json
.venv/Scripts/python.exe Application/benchmark_equipment_identity.py --limit 2861 --output docs/identification-rapide-2026-11-08/benchmark-final.json
.venv/Scripts/python.exe outils/benchmark_identification_captures.py --output docs/identification-rapide-2026-11-08/captures.json
```

Exécuter les benchmarks sans la suite de tests en parallèle. Les temps varient
selon la machine et les caches du système. Les résultats JSON conservent la
version Python et le système pour le banc des références.

## Fichiers livrés et limites restantes

Nouveaux modules : `forgely_equipment_identity.py`, `forgely_icon_audit.py`,
`benchmark_equipment_identity.py`. Intégration : `forgely_item_identity.py`,
`forgely_continuous_identity.py`, `forgely.py`. Deux nouveaux fichiers de tests
couvrent le moteur et les décomptes de l'audit. Diagnostic réel reproductible :
`outils/benchmark_identification_captures.py`. Le manifeste `sources-sha256.json`
identifie les versions livrées.

Pas de nouveau binaire Windows construit, pas de publication distante, pas de
commit local possible dans ce dossier sans métadonnées Git. La reconnaissance
générale en jeu et l'extraction automatique de catégorie restent à valider ;
le résultat livré garantit des décisions conservatrices dans les cas testés,
pas une reconnaissance de tous les équipements DOFUS 3.
