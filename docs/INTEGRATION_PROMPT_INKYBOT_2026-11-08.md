# Intégration du contrat de conseil — 8 novembre 2026

Le prompt adapté est enregistré dans `Application/PROMPT_CONSEILLER_FM.md` et
affiché en tête des « Règles du copilote ». L'application conserve son moteur
Python local : aucun modèle conversationnel n'est ajouté et aucun apprentissage
par simple lecture du prompt n'est annoncé.

## Conflits identifiés et résolus

| Point | Arbitrage appliqué |
|---|---|
| Prix réintroduits dans le classement | `advise` et `candidates` ignorent les paramètres économiques hérités ; aucune estimation de prix dans leur résultat. |
| Ancien mode Budget optimisé | Migration vers Chances maximales ; référence de prix conservée comme donnée historique, sans effet sur le conseil. |
| Blocage possible par budget en kamas | Le chemin actif `strategy_current` ne passe plus par le filtre budgétaire. |
| Paramètres et menu encore économiques | Entrée dédiée retirée du menu ; réglages du conseil reformulés sans promesse de progression par kama. |
| Phase de puits remplaçant les séquences | Lorsque tous les candidats ont une évaluation de séquence comparable, le classement déjà établi est conservé ; la phase devient descriptive. |
| Probabilité de la prochaine rune confondue avec objectif complet | Les séquences du jet complet priment ; les explications distinguent modèle local et probabilité officielle. |
| Réserve double du déficit chez Inkybot | Documentée comme heuristique, sans imposer le coefficient deux au moteur. |
| Poids et plafond 101 | Référentiel Forgely conservé ; le plafond n'est pas un plafond du puits ni un budget universel partagé. |
| Pondération 60/40 face au posterior calibré | Pas de double application des mêmes observations ; repli et poids effectifs explicités. |
| Prompt autorisant un puits estimé | Le moteur actif garde son exigence de puits confirmé ; un intervalle incertain reste informatif. |
| Valeur exacte ou intervalle | Non revendiqués par l'interface numérique actuelle : ses objectifs restent des minimums. |
| Plus aucun candidat | État bloqué conservé ; jamais assimilé à objectif atteint. |

Les anciens fichiers de prix et outils de compatibilité restent conservés.
Leur suppression physique n'est pas nécessaire pour neutraliser leur effet dans
le conseiller. Les profils et sessions d'entraînement existants ne sont pas effacés.
La validation des politiques reste liée au code du sélecteur : un ancien audit
ne certifie pas automatiquement ce nouveau sélecteur.

## Validation ciblée

95 tests réussis sur le contrat, la matrice de puits, les séquences, les candidats,
les anciens prix, les objectifs, l'intégration du conseiller, les préférences,
les règles expertes et les estimations du modèle. Deux régressions ont été
reproduites avant correction : un changement de prix changeait le conseil,
et la phase de puits écartait le meilleur candidat de séquence.

Compilation Python des modules modifiés vérifiée. L'affichage des règles est
testé via sa fonction de production ; aucune validation visuelle de la fenêtre
Windows n'est revendiquée. La recette PyInstaller inclut le nouveau prompt,
mais aucun exécutable n'a été reconstruit.

Utiliser le lanceur `LANCER_FORGELY_MIS_A_JOUR.bat` et redémarrer l'application
pour charger ces sources. Les anciennes distributions ne sont pas mises à jour.

## Vérification globale finale

1759 passed, 27 skipped, 42 subtests passed in 108.82s (0:01:48)

Exécution complète avec un dossier temporaire autorisé et Tesseract ajouté au PATH du processus de test. Aucun réglage système permanent modifié. Les anciennes assertions économiques ont été adaptées au contrat demandé ; le test de bilan de session utilise maintenant la rune effectivement conseillée.
Les tentatives précédentes avaient signalé des erreurs de répertoire temporaire, deux tests OCR sans Tesseract dans le PATH et des attentes économiques devenues obsolètes. La dernière exécution complète ci-dessus remplace ces résultats intermédiaires.
