# Moteur hybride Forgely

Le module Application/forgely_hybrid.py réutilise le moteur DoFocus et ForgemagingEnv. Il ne présente pas les règles du simulateur comme des probabilités officielles du jeu.

## Utilisation

```python
from forgely_hybrid import ItemState, EmpiricalCorrector, DecisionEnvironment
from forgely_data import DB_FILE

state = ItemState("Nom exact de l’objet", [
    {"stat": "Force", "value": 19, "min": 10, "max": 20, "weight": 1}
], pool=3.5, level=200)
corrector = EmpiricalCorrector(DB_FILE, minimum=30, prior_strength=100)
env = DecisionEnvironment(state, {"Force": 20}, corrector=corrector,
                          prices={"Fo": 100}, budget=10000, seed=7)
observation = env.reset(seed=7)
observation, reward, terminated, truncated, info = env.step("Fo")
```

L’exemple minimal n’est pas le profil d’un objet réel. Fournir toutes les lignes naturelles et leur poids depuis le catalogue existant pour un usage réel. Le nom doit correspondre exactement à celui enregistré en base.

## Correction

Lecture seule de fusion_contexts, source local_screen uniquement : jet avant complet et puits strictement identiques, même objet et rune. Ces enregistrements proviennent du suivi confirmé existant ; le correcteur ne certifie pas une donnée importée arbitrairement dans cette table. Aucune création de base, migration ou écriture. Une base absente, indisponible ou corrompue entraîne le repli théorique.

À partir de 30 observations, pour chaque résultat :

`P_finale = (100 * P_théorique + n * fréquence_réelle) / (100 + n)`

Les probabilités sont exprimées en pourcentage. Le prior de 100 et le seuil de 30 sont des choix prudents configurables, sans valeur de règle du jeu. Les métadonnées empirical_n et empirical_weight figurent dans info['odds']. Ce correcteur ajuste les fréquences SC/SN/EC ; les pertes conditionnelles et arrondis restent ceux du moteur existant.

Un puits inconnu reste None : une prédiction théorique est possible mais la simulation est refusée. Un puits observé incertain ou inféré ne permet pas de calibration. Les états renvoyés après une étape sont marqués simulation ; ils ne deviennent jamais des observations de joueur. Une trajectoire peut consulter les données réelles compatibles avec ses états hypothétiques, sans les modifier.

## Actions et récompense

get_legal_actions expose les runes admissibles par le modèle avec contraintes de budget/stock. get_valid_actions conserve le masque orienté vers le jet demandé, utilisé par step ; cela évite de changer les contrats de l’entraînement existant. Le coût inconnu reste signalé par price_known=False ; il ne constitue pas un profit mesuré. La récompense existante mesure la progression pondérée vers les cibles, moins le coût connu et un bonus de réussite.

reset retourne une observation ; step retourne cinq valeurs. Aucune dépendance Gymnasium supplémentaire ni promesse de conformité à gymnasium.Env. Un adaptateur de spaces/reset sera nécessaire pour les bibliothèques exigeant cette classe.

## Conseils et déploiement

combine_candidate_evidence accepte simulation_weight, initialement 0.4 (réel : 0.6). Ce mélange de scores de conseil est indépendant du lissage empirique. Le correcteur est optionnel dans DecisionEnvironment : il n’est pas activé automatiquement dans les conseils, dans l’exécutable ou dans les entraînements historiques. Cela évite une double utilisation des mêmes données réelles et préserve les anciens checkpoints. Son activation demande un raccord explicite via l’API ci-dessus.

## Validation et limites

Les tests vérifient repli, séparation de sources, appariement exact, lissage, distribution du tirage, reproductibilité, actions et pondération. Le projet dispose déjà de forgely_validation_predictive.validate_temporal pour l’évaluation chronologique réelle, mais cet évaluateur estime des fréquences empiriques : il ne constitue pas à lui seul une évaluation du nouveau correcteur hybride.

Aucune amélioration réelle ou calibration indépendante du nouveau correcteur n’a été mesurée ici. Avant une activation généralisée, figer les données de calibration et évaluer le modèle hybride sur d’autres sessions complètes, sans leur accès depuis le correcteur. Les tables historiques ne stockent pas la version des bornes naturelles ni un identifiant de session : l’appariement suppose une identité stable de l’objet. L’appariement exact sera souvent peu couvert. Ne pas lancer un entraînement massif pour conclure à une précision en jeu.

## Vérification du 7 novembre 2026

Suite complète : 1 306 tests réussis, 24 ignorés et 42 sous-tests réussis. Les premiers échecs provenaient du répertoire temporaire inaccessible et de Tesseract absent du PATH de test ; la suite complète passe après configuration locale du processus de test. Le rapport automatisé est joint à l’archive de sources. Aucun binaire recompilé et aucune validation dans une session DOFUS active.
