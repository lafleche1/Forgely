# Accès au jet souhaité

La définition d'une cible ne doit pas dépendre de la validation du jet complet
nécessaire aux conseils. Le lecteur avait conservé cette dépendance dans deux
chemins : l'ouverture du formulaire et son invitation automatique.

Correction :

- Une lecture partielle stabilisée du logement courant peut ouvrir l'éditeur.
- L'invitation automatique n'attend plus un snapshot complet. Une seule
  invitation est planifiée à la fois et les cibles déjà définies sont conservées.
- Le bouton « Jet cible » est visible en permanence dans le copilote, à côté
  d'Atelier, Observer et Détails. Le menu existant est conservé.
- L'enregistrement reste lié à la révision de l'objet. Changer d'objet pendant
  l'édition ne permet pas d'appliquer les cibles à l'ancien objet.
- La lecture partielle utilisée pour saisir une cible n'autorise jamais, à elle
  seule, un conseil ou un exemple d'apprentissage.

Le test `Tests/test_goal_access_regression.py` exerce un vrai formulaire Tk :
invitation automatique avec OCR incomplet, saisie, clic d'enregistrement,
affichage des cibles, puis réouverture depuis le bouton visible. Il vérifie
également que les lectures périmées et celles d'un autre compte sont exclues.
Ces tests complètent ceux de l'OCR ; ils ne remplacent pas une validation en jeu.

Le cas terrain 162925 couvrait un second lien manquant : le formulaire prenait
le focus avant la fin de l'identification automatique, donc « Jet parfait »
n'avait pas de référence théorique. L'éditeur résout désormais l'objet depuis
le logement courant de la capture, vérifie sa concordance avec l'icône de la
session et conserve cette référence de catalogue pour la durée de l'édition.
Cette référence est effacée au changement d'objet ; elle n'autorise pas une
lecture numérique périmée. Le nom de l'historique n'est pas utilisé.

Le test terrain ouvre le vrai formulaire avec une identité automatique encore
en attente, active Jet parfait, contrôle 300 Vitalité / 40 Force / 10 Dommages
Neutre, enregistre les cibles et vérifie le calcul d'un conseil quand un jet
complet est ensuite fourni. Le contrôle Jet parfait global conserve également
les cibles de cette session. Les sources d'apprentissage de l'historique sont
conservées et restent soumises aux contrôles des états avant/après.
