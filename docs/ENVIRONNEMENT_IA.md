# Environnement de forgemagie pour l'IA

`Application/forgely_rl.py` expose `ForgemagingEnv`, sans dépendance supplémentaire.
Le contexte du simulateur existant fournit `context.environment(seed=42)`.
Chaque environnement possède son jet, son générateur aléatoire et ses ressources.
Il ne modifie ni la capture en cours ni les observations réelles.

```python
env = context.environment(seed=42, max_steps=200)
state = env.get_state()
actions = env.get_valid_actions()
state, reward, terminated, truncated, info = env.step(actions[0])
```

- `get_state()` : jet détaillé, bornes naturelles, objectifs, puits numérique
  sans arrondi supplémentaire, confiance, budget, stock, prix et vecteur.
  Le vocabulaire des caractéristiques est fixe ; des masques distinguent
  une valeur absente d'un zéro. Le vecteur est accompagné du nom de ses variables.
- `get_valid_actions()` : runes des caractéristiques ciblées encore déficitaires,
  sans dépasser la cible, contrôlées par les limites du moteur Dofocus au niveau
  de l'objet. Aucun seuil de niveau supplémentaire n'est inventé. Les prix inconnus
  sont exclus si un budget est imposé. Un stock fourni limite les runes disponibles.
  `stop` permet de terminer. Cette politique volontairement ciblée n'explore pas
  les sacrifices temporaires de caractéristiques déjà satisfaites.
- `step(action)` : tirage SC/SN/EC par le moteur local, pertes, nouveau puits,
  consommation des ressources, récompense et fin d'épisode. Une action invalide
  ne modifie pas l'état. `reset(seed=...)` restaure l'épisode initial.

La récompense est la diminution du déficit pondéré vers les cibles, moins
le prix de la rune divisé par `cost_scale` (1000 par défaut), plus 50 lors
du premier franchissement de tous les objectifs. Dépasser une cible ne rapporte
aucun gain supplémentaire. Consommer utilement le puits n'est pas pénalisé.
Sans prix renseigné, le coût est nul et `price_known` vaut faux : cela ne mesure
donc pas une rentabilité économique. La limite de tentatives tronque l'épisode.

Le travailleur de simulation existant calcule également `mean_reward` dans
ses résultats virtuels, conservés par son journal existant. Le classement
actuel reste fondé sur ses critères existants ; ce score n'est pas un taux de réussite.
Les essais existants peuvent évaluer des runes dépassant la cible : le masque
de l'environnement d'entraînement est volontairement plus strict.

Toutes les transitions `step` portent `source=simulation`, `real_observation=False`,
la version du moteur et celle de la récompense. Aucun essai virtuel n'est ajouté
aux observations réelles. Le puits est exact dans le modèle, pas garanti exact
par rapport à une lecture OCR. La confiance est descriptive : le simulateur
n'invente pas de distribution d'incertitude sur le puits.

Cette intégration fournit l'environnement et le score pour entraîner un agent.
Elle n'entraîne pas encore un réseau neuronal et ne lance pas de millions
d'épisodes automatiquement. Le modèle reproduit les mécanismes étudiés du
simulateur Dofocus ; sa fidélité au jeu doit être évaluée sur des essais réels.
