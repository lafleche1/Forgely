"""Hybrid adapter: empirical outcomes, existing Dofocus transitions.

Percentages describe a simulator, never official game probabilities. Exact
matching deliberately prefers no correction over pooling incompatible states.
This module never writes observations or trains itself on simulated outcomes.
"""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3
from contextlib import closing

from forgely_dofocus import RUNE_CHOICES, reference
from forgely_dofocus_engine import odds, attempt, _validate, _number, MODEL_VERSION
from forgely_rl import ForgemagingEnv


@dataclass
class ItemState:
    item: str
    lines: list
    pool: float | None
    level: int = 200
    pool_source: str = 'observed'
    pool_confidence: float = 1.0

    def __post_init__(self):
        _validate(self.lines, {'stat':'Force','gain':1,'weight':1}, self.level)
        if not isinstance(self.item,str) or not self.item.strip():
            raise ValueError('Identité requise')
        if self.pool is not None and (not _number(self.pool) or not 0<=self.pool<=30000):
            raise ValueError('Puits invalide')
        if not _number(self.pool_confidence) or not 0<=self.pool_confidence<=1:
            raise ValueError('Confiance invalide')
        if self.pool_source not in ('observed','simulation','inferred','unknown'):
            raise ValueError('Provenance invalide')
        self.lines=deepcopy(self.lines)
        if self.pool is None:
            self.pool_source='unknown'
            self.pool_confidence=0.0


def rune_spec(rune):
    stat=next((s for s,rs in RUNE_CHOICES.items() if rune in rs),None)
    if stat is None:
        raise ValueError('Rune inconnue')
    ref=reference(rune)
    return {'stat':stat,'gain':ref.gain,'weight':ref.weight}


class TheoreticalEngine:
    model_version=MODEL_VERSION

    def predict_outcome(self, item_state, rune):
        return odds(item_state.lines,rune_spec(rune),level=item_state.level)


class EmpiricalCorrector:
    """Read confirmed local contexts only; shrink exact frequencies to a prior.

    Pool confidence must be 1 and observed. Existing records have no historical
    natural-bound version: item identity is assumed stable in this local DB.
    minimum=30 and prior_strength=100 are configurable safeguards, not game rules.
    """
    def __init__(self, db_file, *, minimum=30, prior_strength=100.):
        if type(minimum) is not int or minimum<1:
            raise ValueError('Seuil invalide')
        if not _number(prior_strength) or prior_strength<=0:
            raise ValueError('Prior invalide')
        self.path=Path(db_file)
        self.minimum=minimum
        self.prior_strength=prior_strength

    def get_adjusted_probabilities(self, item_state, rune, theoretical_probs):
        base=dict(theoretical_probs)
        if (base.get('blocked') or item_state.pool is None
                or item_state.pool_source!='observed' or item_state.pool_confidence!=1
                or not self.path.is_file()):
            return base
        jet={line['stat']:line['value'] for line in item_state.lines}
        counts={'SC':0,'SN':0,'EC':0}
        try:
            with closing(sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.1)) as db:
                rows=db.execute("SELECT outcome,before_json FROM fusion_contexts WHERE item=? AND rune=? AND source='local_screen'",(item_state.item,rune))
                for outcome,raw in rows:
                    try:
                        before=json.loads(raw)
                        if (outcome in counts and isinstance(before,dict)
                                and before.get('jet')==jet and before.get('pool')==item_state.pool):
                            counts[outcome]+=1
                    except (ValueError,TypeError):
                        continue
        except sqlite3.DatabaseError:
            # Missing schema, corruption or a busy DB must not interrupt the observer.
            return base
        n=sum(counts.values())
        if n<self.minimum:
            return base
        for key in ('sc','sn','ec'):
            base[key]=(self.prior_strength*base[key]+100*counts[key.upper()])/(self.prior_strength+n)
        base.update(empirical_n=n,empirical_weight=n/(self.prior_strength+n),
                    empirical_source='local_screen_exact',estimated=True)
        return base


class DecisionEnvironment(ForgemagingEnv):
    """Existing goal-guided environment with optional calibrated outcome draws.

    step returns observation/reward/terminated/truncated/info. reset returns an
    observation, so this is not a gymnasium.Env subclass. In simulation the pool
    remains numerically exact but represents a model, not a game observation.
    """
    def __init__(self, item_state, targets, *, corrector=None, **kwargs):
        if item_state.pool is None:
            raise ValueError('Un puits connu est nécessaire pour simuler')
        self.item=item_state.item
        self.corrector=corrector
        self._pool_source=item_state.pool_source
        self._pool_confidence=item_state.pool_confidence
        super().__init__(item_state.lines,item_state.pool,targets,level=item_state.level,
                         confidence=item_state.pool_confidence,**kwargs)

    def get_state(self):
        state=super().get_state()
        state.update(item=self.item,pool_source=self._pool_source if self.steps==0 else 'simulation',
                     pool_confidence=self._pool_confidence)
        return state

    def get_legal_actions(self):
        """Model-admissible runes, including ones outside the requested target.

        step intentionally keeps the existing goal-guided action mask; callers
        may inspect this wider list without authorizing unwanted over/exo.
        """
        if self.closed:
            return []
        actions=[]
        for names in RUNE_CHOICES.values():
            for rune in names:
                if self.stock is not None and self.stock.get(rune,0)<=0:
                    continue
                if not odds(self.lines,rune_spec(rune),level=self.level).get('blocked'):
                    actions.append(rune)
        return actions+['stop']

    def _attempt(self, action):
        state=ItemState(self.item,self.lines,self.pool,self.level,
                        self._pool_source,self._pool_confidence)
        # Simulated states are query contexts, never observations added to DB.
        base=TheoreticalEngine().predict_outcome(state,action)
        final=self.corrector.get_adjusted_probabilities(state,action,base) if self.corrector else base
        return attempt(self.lines,self._spec(action),self.pool,level=self.level,
                       rng=self.rng,probabilities=final)
