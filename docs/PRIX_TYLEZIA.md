# Prix moyens de référence — Tylezia

Les 105 noms et prix proviennent des captures HDV fournies par l'utilisateur
dans cette session, reçues le 8 novembre 2026. La date précise de calcul du prix
moyen par DOFUS n'est pas connue. Aucun prix n'est récupéré sur un site tiers.
Le champ « Prix moyen » est déjà unitaire : aucune division par lot n'est faite.
Le fichier `Application/prices/tylezia-2026-11-08.json` contient toutes les valeurs.

Au premier lancement, la grille est installée dans les préférences locales,
le serveur est marqué Tylezia et le mode **Budget optimisé** est sélectionné.
Les préférences précédentes sont conservées dans
`atelier_preferences.avant-tylezia-2026-11-08.json`, à côté des préférences actives.
Les démarrages suivants respectent les corrections manuelles et le mode choisi.

Le mode économique existant classe les runes selon la progression vers le jet
demandé et leur prix, avec une pénalité indicative de réparation faute de puits.
Les contraintes de FM et l'arrêt lorsque l'objectif est atteint restent actifs.
Ce classement est une heuristique : il ne garantit ni le coût minimal final, ni
un taux de réussite. Le prix moyen n'est pas une offre d'achat immédiatement
disponible. Il ne s'actualise pas automatiquement et ne vaut que pour Tylezia.

Les prix restent modifiables dans **Prix des runes et budget**, ou dans
**Outils → Stratégie et kamas**. Le budget 0 signifie sans limite.
Le mode **Chances maximales** reste sélectionnable : il ne classe pas selon le
prix, mais respecte un budget si celui-ci est renseigné.
Les observations et l'entraînement ne sont jamais modifiés par cet import.

## Installer la mise à jour locale

Fermer Forgely. Extraire le contenu de `Forgely-prix-Tylezia.zip` dans le dossier
qui contient `OUVRIR FORGELY.bat` et `Application`, puis lancer
`METTRE_A_JOUR_PRIX_TYLEZIA.bat`. Les fichiers remplacés sont sauvegardés.
Le script refuse une version locale différente de la base attendue ; il ne
force jamais l'écrasement des modifications locales. La mise à jour vise une
installation à partir des sources actuelles de GitHub, pas un ancien EXE seul.
Relancer `OUVRIR FORGELY.bat` pour activer les prix et le mode économique.

Pour une installation depuis la dernière archive GitHub, le démarrage habituel
suffit : la migration des prix est intégrée à l'application.
