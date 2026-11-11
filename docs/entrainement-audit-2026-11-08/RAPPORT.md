# Audit de l'entraîneur Forgely — 8 novembre 2026

## Sources et portée

Le rapport de la conversation a été relu : 100 entraînements, puis 1/200 jets
complets pour la politique et 3/200 pour le témoin. Ces quatre succès ne prouvent
ni une supériorité ni une infériorité statistique. Aucun changement de taux
probabiliste n'est justifié par ces seuls agrégats.

Les sources locales étaient déjà disponibles, sans métadonnées Git. Le connecteur
GitHub a renvoyé 404 pour `lafleche1/Forgely` (fichier
`Application/forgely_training.py`). L'accès privé ou l'existence de ce chemin
ne peut donc pas être confirmé. Aucun push ni commit distant.

L'EXE local n'a pas été exécuté. Analyse statique : PE Windows x86, 161792 octets,
non signé ; empreinte et chaînes sélectionnées dans `exe-static.json`.
Les chaînes concordent avec le lanceur C# local (pythonw.exe et
Application/entrainer_forgely.py), sans prouver l'équivalence du binaire aux
sources ni son innocuité. `/mnt/data/Entrainement_Forgely.exe` est indisponible
sur cet hôte Windows : identité avec la pièce jointe non établie.

## Diagnostic et correction

La clé de la table Q regroupait les caractéristiques légères dans 16 classes,
le puits par tranches de 2 et l'horizon dans 16 classes ; elle ignorait le stock.
Exemple reproduit : Vitalité 285 et 286, plafond 300, même clé malgré Pa Vi légale
seulement dans le premier état. Un puits 0 et 1, ainsi que 100 et 99 tentatives
restantes, partageaient aussi leur clé. Ce défaut introduisait des transferts
de valeurs Q entre situations dont les décisions ou transitions diffèrent.

La clé conserve maintenant valeurs exactes, puits, horizon relatif exact et
stock normalisé. La configuration vérifie séparément cibles, profil et horizon
maximum. La version de politique devient `exact-state-no-currency-6` : les
anciennes archives restent sur disque mais leurs tables ne sont pas réutilisées.
L'audit refuse également les anciens formats au lieu de les lire avec une clé
incompatible. La limite existante de 50 000 états et le repli heuristique restent
actifs. Contrepartie : la couverture des états peut diminuer ; une amélioration
de performance doit être mesurée, elle n'est pas déduite de cette correction.

Six tests ajoutés : frontières de légalité, puits, horizon, stock, équivalence
entier/flottant, refus des anciennes politiques. Les quatre reproductions ont
échoué avant correction ; aucune modification du moteur n'a servi à les forcer.

## Moteur, puits, récompense et sélecteur

Le moteur partagé calcule SC/SN/EC et traite séparément les pertes. Le puits est
consommé sur SN/EC et les pertes excédentaires peuvent le recréer ; SC ne le
consomme pas. Les over/exos et profils signés sont soumis aux gardes existantes.
Ces comportements sont ceux du modèle local, pas une validation des règles
exactes du jeu. Les pertes de repli et probabilités restent des hypothèses
à confronter à des transitions réelles confirmées. Aucun taux officiel inventé.

La récompense donne le bonus au jet complet ; son potentiel télescopique est
annulé à l'échec terminal, et les mises à jour ne le discountent pas. Les tests
existants couvrent abandon, progression partielle, priorité au jet complet et
absence d'effet des prix. Pas de défaut démontré justifiant une nouvelle reward.

Le sélecteur exige un gain sur jets complets et un audit distinct portant sur
son code, ses réglages et le contenu de la politique. Le changement de version
et d'empreinte invalide les anciennes validations. Les benchmarks ci-dessous
n'activent rien et ne remplacent pas cet audit du conseil final.

## Préservation et livraison

Seuls `Application/forgely_training.py`, `Application/auditer_politique.py` et
le nouveau test sont modifiés/ajoutés en production et tests. Copies avant
modification dans ce dossier. Les essais écrivent leurs propres archives ici,
sans reprise des archives utilisateur et sans données réelles. Aucun ancien
checkpoint supprimé, aucune observation réelle ajoutée, aucune politique activée.
L'EXE n'est ni remplacé ni reconstruit. Les lanceurs de sources existants doivent
être utilisés pour bénéficier des changements.

## Validation

Voir `tests.log`/`tests.xml` pour la suite générale et `focused.log`/`focused.xml`
pour le périmètre entraîneur/FM. La première tentative ciblée a rencontré des
erreurs de dossier temporaire ; les exécutions suivantes utilisent un dossier
temporaire du workspace.

La suite générale a donné 1735 tests réussis, 27 ignorés, 42 sous-tests réussis
et quatre échecs :

- Application/tests/test_display_modes.py::DisplayModes::test_mode_switch_invalidates_old_ocr_even_with_same_visual_signature
- Application/tests/test_identity_latency.py::IdentityLatencyTests::test_identity_worker_delivers_before_full_ocr_is_called
- Application/tests/test_identity_latency.py::IdentityLatencyTests::test_unreadable_static_heading_requests_a_fresh_retry_capture
- Application/tests/test_identity_latency.py::IdentityLatencyTests::test_unresolved_fast_name_does_not_consume_full_fallback_frames

Les erreurs concernent un snapshot absent et un attribut `capture` absent dans
les objets de test. Elles se trouvent dans des chemins non modifiés par cette
intervention ; aucune suite générale entièrement verte n'est revendiquée.
Cette exécution précède l'ajout des deux derniers tests et le refus explicite du
format d'audit historique ; la suite ciblée couvre ces derniers changements.

## Benchmark reproductible

`benchmark.py` compare la copie avant correction et les sources corrigées :
100 entraînements, horizon 130, cibles du rapport, jet moyen, puits 0, puis deux
audits figés de 200 épisodes par bras, graines 314159 et 271828. Les graines
indépendantes ne servent ni à entraîner ni à sélectionner de nouveau candidat.
La graine d'entraînement est 20261107 ; domaines RNG séparés. L'archive originale a ensuite été retrouvée dans Entrainements : elle confirme
les résultats fournis et un horizon 200. Notre comparaison a été fixée avant cette découverte à
un horizon 130 et aucune donnée réelle ; ce n'est pas sa reproduction exacte.
Son résumé et son empreinte sont dans original-checkpoint-summary.json. Les fichiers before/after conservent tous les résultats et checkpoints.

Suite ciblée finale : **134 réussites, 1 ignoré**, incluant les six nouveaux tests.

## Ce qui n'est pas établi

L'audit complet du sélecteur sur le Cycloïde n'a pas été exécuté dans cette
intervention. Ses garde-fous ont été testés ; aucune autorisation d'activation
n'en est déduite. Les benchmarks portent sur la politique directe figée.
Il n'y a pas de validation en jeu, de calibration officielle, de reconstruction
vérifiée de l'EXE joint, ni de publication GitHub. Un entraînement plus long ou
une politique généralisable peuvent être étudiés ultérieurement, avec un nouvel
échantillon de validation ; ils ne sont pas présentés comme des gains acquis.

Les changements sont également fournis dans `modifications.patch` ;
`source-hashes.json` identifie les sources de la livraison. Compilation Python
réussie des deux modules modifiés, du nouveau test et du script de benchmark.

## Résultats finaux du benchmark

| Graine indépendante | Avant : jets complets | Après : jets complets | Témoin |
| --- | ---: | ---: | ---: |
| 314159 | 3/200 | 1/200 | 1/200 |
| 271828 | 1/200 | 0/200 | 1/200 |

Total descriptif : avant 4/400, après 1/400, témoin 2/400. Ces faibles nombres
ne démontrent aucun gain. La correction des collisions n'est pas une amélioration
d'apprentissage validée ; les résultats observés après correction sont même
numériquement moins bons. **Aucune politique activée.**

Sur le banc interne de sélection : avant 2/200, après 0/200, témoin 3/200.
Les résultats bruts restent conservés, y compris les échecs. Le libellé de
limitation dans les sources a été ajusté après génération des checkpoints pour
décrire la table exacte à couverture limitée ; ce changement de texte ne change
pas les décisions évaluées. La suite ciblée a repassé sur les sources finales.

L'archive originale comptait 23962 états inconnus sur 24923 décisions apprises
d'évaluation (environ 96 %). La généralisation reste donc un problème ouvert.
