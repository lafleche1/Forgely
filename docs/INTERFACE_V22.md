# Forgely v22.00 — le nouvel atelier

## Présentation

Refonte native Windows/Tkinter avec une palette graphite et émeraude, des accents dorés, une typographie plus nette et une navigation latérale. Le tableau central distingue les valeurs lues des objectifs. L'assistance, les variations récentes et les observations locales disposent d'espaces dédiés.

Le mode flottant reprend cette présentation dans un badge de 270 × 86 pixels. Une lecture candidate y est marquée « À vérifier ». Le retour à l'application, le déplacement et le menu contextuel sont conservés.

## États des données

- Aucune valeur observée n'est affichée au démarrage sans lecture du jeu.
- Une cible enregistrée apparaît avec une valeur actuelle « — » si elle n'a pas été lue.
- Une lecture provisoire n'indique jamais qu'une cible est atteinte.
- Les valeurs de l'équipement et le puits sont retirés après fermeture de l'atelier ou changement de compte.
- Le fil de lecture est un aperçu visuel des derniers états, limité à huit entrées ; l'historique des tentatives reste disponible séparément.

Les moteurs de capture, OCR et décision ainsi que les données locales existantes restent utilisés. Cette version ne prétend pas avoir validé le délai rune → affichage sous Windows.

## Apparence et accès aux outils

Le thème émeraude remplace l'ancien thème par défaut. Les thèmes précédents restent proposés ; un choix explicite du thème classique est mémorisé. Le changement de palette recolore le tableau et le badge sans redémarrer l'observation.

Navigation : Atelier, Jet cible, Historique, Outils. Les paramètres, le diagnostic OCR et l'apparence sont accessibles directement en bas de la barre latérale. Le menu Outils conserve notamment le référentiel théorique, les sauvegardes, les budgets et les réglages de détection.

## Validation

Validation locale : 311 tests réussis, 6 tests nécessitant des captures absentes ignorés, 19 sous-tests réussis ; les huit tests graphiques sont exécutés séparément sur un bureau Tk réel et passent. Le lancement à vide, les dimensions 1180 × 780 et 960 × 660, le tableau provisoire/confirmé, les changements de compte et d'atelier, les cinq palettes et le fil de lecture sont contrôlés.

Inspection visuelle réelle du tableau de bord et du mode flottant, avec retour à l'application. Le workflow GitHub vérifie les widgets Tk sous Xvfb en plus de la suite normale. Le rendu Windows et ses facteurs de mise à l'échelle restent à tester sur la machine de l'utilisateur.
