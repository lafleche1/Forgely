# Obsidienne Implementation Plan

Goal: appliquer le choix explicite Obsidienne + Copilote dans l’application existante.

Architecture: palette unique dans forgely_themes.py ; atelier et fenêtre flottante partagent les mêmes lectures qualifiées, sans nouvelle capture.

Tech Stack: Python, Tkinter, ttk.

Spec: ../specs/2026-11-07-obsidienne-design.md

- [x] Tester la migration des anciens thèmes et la persistance d’Obsidienne ; supprimer les anciennes palettes.
- [x] Simplifier les commandes d’affichage ; adapter la palette et la lisibilité de l’atelier.
- [x] Transformer le badge en Copilote compact avec tableau défilant, puits, statut et dernières lectures.
- [x] Vérifier la synchronisation provisoire et la disparition des valeurs périmées ; tester l’interface et la suite existante.

Review focus: anciennes préférences, atelier fermé, lecture provisoire, petite fenêtre, retour du panneau compact vers l’atelier.

Validation : suite générale 1319 réussis, 25 ignorés, 42 sous-tests. Les tests graphiques ciblés couvrent les valeurs provisoires, les données périmées, la petite fenêtre et le sélecteur. Le test graphique Dofocus a été interrompu par la destruction de la fenêtre pendant Tk.update ; il ne peut pas être déclaré validé.
