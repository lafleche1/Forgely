# Atelier mobile et jet sur plusieurs pages

Objectif : conserver les lignes confirmées d'un même objet pendant le défilement,
sans présenter un jet incomplet ou ancien comme actuel.

Architecture : conserver le repérage adaptatif existant de l'application. Ajouter
une mémoire par caractéristique et contexte d'objet dans WorkshopReadings ;
afficher les états par ligne dans le tableau. Pour la V1 OpenCV, chercher les
gardes de libellé dans toute la zone des caractéristiques au lieu de leur ancien
emplacement et accepter plusieurs profils natifs d'interface.

Contraintes : aucun chiffre déduit d'une fiche théorique ; zéro reste une valeur
lue. Ne pas assembler des contextes d'objets différents. Après une tentative ou
une variation constatée, les valeurs hors écran deviennent à revérifier. Une
fusion de pages sert aux conseils uniquement après confirmation du profil
nécessaire ; elle ne prouve pas une transition atomique pour l'apprentissage.

- [x] Tests de fusion, zéro, négatifs, changement d'objet, valeurs périmées,
  alias, profil absent et répétition d'une capture.
- [x] Mémoire paginée et intégration à la lecture et au tableau de l'application.
- [x] Tests puis lecteur OpenCV par libellé mobile et sélection de profils natifs.
- [x] Vérification ciblée, suite complète et documentation des limites de calibration.

Le moteur OCR actif n'est pas remplacé : le dictionnaire V1 reste partiel et ne
décode pas encore les tentatives du journal. Voir `docs/Vision_Atelier_Adaptatif.md`.

Risques à vérifier : infobulles, libellés similaires, doublons, redimensionnement
non calibré et tentative intervenue avant réception de son événement.
