# Forgely 0.20.35 — Identification robuste après rune

- Les deux vues OCR du nom de l'objet sont désormais lues indépendamment, même si la première ne renvoie rien. Une seule vue lisible fournit un **candidat provisoire** ; elle ne crée jamais un objet immédiatement.
- Le second passage évite davantage les pixels du logo à gauche du texte.
- La confirmation nom + logo accepte une ou deux captures OCR illisibles entre des lectures cohérentes ; elle exige toujours au moins quatre lectures positives du même nom et du même logo. Trois absences successives réinitialisent la confirmation.
- Deux noms contradictoires restent rejetés ; l'enregistrement d'un logo différent d'un logo existant reste bloqué.
- Le diagnostic indique le nombre de confirmations et d'absences OCR ; l'export diagnostic inclut les lectures du nom et le statut du logo.
- Les informations de jet/puits provisoires n'affichent plus systématiquement « attente de première rune » si l'historique contient déjà des tentatives.
- La capture Windows, la reconnaissance « Atelier OUI », le lanceur à un clic et les données locales sont inchangés.

Limite : ce correctif cible les lectures OCR intermittentes ; un éventuel conflit avec une icône déjà enregistrée doit être diagnostiqué avec les lignes « ÉQUIPEMENT OCR », « CANDIDAT OBJET » et « LOGO OBJET ». Le fonctionnement en jeu sur Windows n'a pas été validé dans cet environnement.
