# Lecture des effets à zéro — 8 novembre 2026

Demande : corriger le panneau « Dommages Terre : À lire » sur la capture de
20 h 48. La capture présente des effets à zéro en blanc, avec un libellé
singulier « Dommage », contrairement aux effets positifs verts.

Diagnostic : le moteur actuel lit bien Terre=0 sur plusieurs cadrages de cette
image. En revanche, sur le cadrage brut il transcrit systématiquement Feu comme
« O Dommage Feu » et omet cette caractéristique du jet. Un jet partiel peut
maintenir la lecture globale en attente. Le cadrage normalisé peut donner un
autre résultat ; la capture seule ne permet pas de reconstituer exactement
l'état du processus qui affichait « À lire ».

Correction dans `Application/forgely_jet.py` : repérer les lignes blanches dans
les bandes d'effets, les recadrer sans les colonnes Min/Max, puis relire le
nombre et le libellé avec deux prétraitements. Seul un zéro numérique explicite
et concordant est récupéré ; ni une lettre O, ni le profil théorique, ni une
ligne absente ne peuvent fournir une valeur. La récupération est bornée à
quatre lignes et deux lectures par ligne, sur un défaut du cache de zone.
Les confirmations temporelles existantes restent nécessaires.

La revue a relevé que le parseur historique transforme O Tacle en zéro. Le
nouveau chemin vérifie donc en plus la présence littérale du chiffre zéro
devant le même libellé, avant de récupérer quoi que ce soit.

Régression : `Tests/test_zero_damage_capture.py`, avec une fixture recadrée sur
la table de la capture fournie. Les cinq tests vérifient les valeurs Terre=0,
Feu=0, Air=9, Vitalité=279, Tacle=2 ; le rejet des désaccords et des lettres O ;
et une omission volontaire de Terre dans l'OCR global, suivie de sa récupération
et de son affichage à zéro après trois lectures stables.

Le groupe ciblé de 17 tests (capture, isolation Min/Max et récupération des
lignes) passe. Le journal du dernier passage complet est dans
`.test-tmp/zero-damage-pytest-final.log`.

Pour appliquer la modification à une application déjà ouverte, fermer Forgely
puis le relancer avec `OUVRIR FORGELY.bat`. Le processus Python charge ses
modules au démarrage ; modifier les sources ne recharge pas le processus en cours.
