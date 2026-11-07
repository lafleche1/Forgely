# Forgely 0.20.3 — laboratoire en arrière-plan

Le laboratoire est **un composant distinct** (`forgely_labo_live.py`), exécuté dans un thread de calcul local lorsque Forgely démarre. Il n’ajoute aucun panneau ni aucune simulation à l’application. Il lit la base SQLite des transitions avant/après déjà capturées par Forgely, sans effectuer une deuxième capture ni ralentir l’OCR. Une nouvelle transition réveille le laboratoire pour actualiser les fréquences.

La recommandation principale reste pilotée par les contraintes du jet et du puits. Le laboratoire ajoute seulement une **estimation descriptive** si au moins 30 transitions ont le même équipement, la même rune, la même tranche de puits et les mêmes caractéristiques OCR présentes. Il affiche les fréquences SC/SN/EC et un intervalle de Wilson, sans prétendre prédire avec certitude la prochaine issue. Les taux n’influencent pas encore le choix de rune : cela nécessitera des données revues et une validation hors échantillon.

**Attention :** les transitions `local_screen` sont issues de l’OCR et ne constituent pas des observations humaines vérifiées. Les simulations ne sont jamais mélangées à ces données. Les sessions Windows/DOFUS n’ont pas été testées ici ; les tests automatisés ne valident pas l’OCR en jeu.
