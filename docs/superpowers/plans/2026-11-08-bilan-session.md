# Bilan automatique et apprentissage progressif

Autorisé : bouton Terminer et évaluer ma session, bilan exportable, chaque session enrichit automatiquement les données fiables.

Architecture : journal d'évaluation séparé des observations, sessions bornées par curseurs SQL et objet/cibles immuables. Prévisions enregistrées avant le résultat (frame et génération capture), puis liées seulement à un avant/après complet cohérent et à la rune réellement jouée. Ne pas reconstruire a posteriori une prévision. Score Brier et taux observés séparés de l'atteinte du jet et des éventuels diagnostics OCR. Aucune classification automatique « mauvais conseil vs malchance » sur un clic isolé.

- [x] SessionRecorder : début automatique à jet/objectif confirmés ; séparation changement objet/cible ; prix figés au début ; clôture idempotente ; JSON+HTML local et ZIP exportable.
- [x] Rapport : minima atteints uniquement si fin confirmée ; runes/résultats/coût connu par curseurs bornés et objet ; actions inconnues non attribuables signalées ; prévisions comparables et diagnostics.
- [x] Journal prospectif : dédoublonnage d'affichages, événement utilisé une fois, contexte/frame/génération stricts, pas de score pour autre rune/lecture partielle/contexte différent.
- [x] Brancher observation et transition, sans ralentir les lectures par écritures répétées ni bloquer l'observation si l'évaluation échoue.
- [x] Bouton accessible + export local ; fermer le bilan ne réinitialise ni budget ni statistiques.
- [x] Apprentissage : les observations qualifiées existantes continuent d'alimenter la calibration, sans réimport de bilan ni résultats virtuels. Conserver seuil30 et prior200 ; chaque session apporte des échantillons mais aucune amélioration monotone garantie.
- [x] Tests de séparation, intégrité, prévision avant résultat, complétude des coûts, export HTML échappé ; revue, suite complète, GitHub et paquet cumulatif.
