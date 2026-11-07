# Correction du diagnostic du 7 novembre — v22.04

Le diagnostic utilisateur montre un jet extrait sans Dommages Feu alors que le texte contient « 1 Dommage Feu ». Le parseur n'acceptait que le pluriel. Cette ligne est maintenant reconnue, avec son signe et sa valeur réellement lus, sans remplacement par une borne théorique.

Une seconde cause est reproductible sans capture privée : la récupération d'un jet incomplet peut essayer jusqu'à 18 paires de bords × 3 variantes OCR, puis 9 bandes × 2 variantes (72 appels supplémentaires dans le pire cas). Une ligne encadrée déjà présente dans le jet ne terminait pas la recherche. Le seuil fixe de 11 lignes ne protégeait pas les jets incomplets ou les petits équipements.

La récupération en direct effectue désormais au plus trois appels OCR supplémentaires par passage. Les résultats intermédiaires sont repris seulement si les pixels, les valeurs déjà lues et la configuration du moteur correspondent exactement. Un changement annule la reprise pour ce nouvel état. Une récupération inachevée demande une nouvelle capture et n'est pas mise en cache comme un échec terminé. Le cache reste limité à quatre états ; les résultats terminés gardent leur durée de validité précédente.

Une ligne encadrée qui confirme exactement une valeur déjà lue termine immédiatement cette récupération, sans balayage des autres bandes. Les tests vérifient qu'une ligne située plus loin dans le balayage est effectivement atteinte au fil des passages, sans dépasser le plafond par passage et sans réutiliser du texte d'une autre image.

Le diagnostic ajoute des durées séparées pour le titre d'atelier, l'historique, les effets, la récupération de lignes, les runes et le reliquat. Ces durées servent à distinguer les prochaines causes de retard plutôt que de conclure à partir d'un seul total.

Limites : la borne de trois appels concerne la récupération supplémentaire en direct, pas toute la lecture d'atelier ni les reprises de titre/première/dernière ligne. Elle ne garantit pas un cycle inférieur à une seconde sur chaque PC. Aucun test réel de délai n'a été effectué sur le poste de l'utilisateur et sa capture n'est pas disponible ici. Le diagnostic montre séparément des numéros de runes sans nom et une vision non calibrée ; ces nombres ne suffisent pas à identifier une rune ou à certifier SC/SN/EC. Aucun résultat de tentative n'est fabriqué.

Validation : cinq régressions nouvelles, 416 tests réussis, 15 ignorés et 25 sous-tests sur la suite complète. Revue indépendante sans problème important signalé. Les tests natifs Tk sont vérifiés séparément sur CI.


L'outil `learn_icon` existait mais n'était plus relié au menu après la refonte. L'entrée **Outils → Calibrer la reconnaissance des runes** est restaurée. Le fichier choisi doit représenter la fenêtre DOFUS entière, au même cadrage que la capture de Forgely ; une zone OCR déjà recadrée ne permet pas de calculer correctement la position relative. La calibration reste locale et ne certifie pas SC/SN/EC.
