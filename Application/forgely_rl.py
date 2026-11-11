"""Offline state/action/reward adapter. Never writes game observations.

API follows reset/step conventions without a dependency on Gymnasium.
Explicit goals authorize over/exo; an opt-in experiment also explores limited
temporary surpluses on existing light lines. stock=None means unlimited stock.
"""
from copy import deepcopy
from math import isfinite
from random import Random
from forgely_dofocus import RUNE_CHOICES, WEIGHT_PER_POINT, reference
from forgely_dofocus_engine import attempt, odds, MODEL_VERSION, _validate

STATE_VERSION = 'forgely-state-no-currency-2'
REWARD_VERSION = 'complete-target-first-2'
STATS = tuple(sorted(WEIGHT_PER_POINT))


def _number(value):
    return type(value) in (int, float) and isfinite(value)


class ForgemagingEnv:
    def __init__(self, lines, pool, targets, *, level=200, prices=None,
                 budget=None, stock=None, confidence=1., max_steps=200,
                 cost_scale=1000., seed=None, allow_preparatory=False, transition_model=None):
        _validate(lines, {'stat':'Force','gain':1,'weight':1}, level)
        if any(x['value']<0 or (x.get('min') is not None and min(x['min'],x['max'])<0) for x in lines):
            raise ValueError('Profil avec malus : règles signées non validées, simulation indisponible.')
        if (not lines or any(x['stat'] not in STATS for x in lines)
                or not _number(pool) or not 0 <= pool <= 30000
                or not isinstance(targets, dict) or not targets
                or any(s not in STATS or not _number(v) or abs(v)>30000 for s,v in targets.items())
                or not _number(confidence) or not 0 <= confidence <= 1
                or type(max_steps) is not int or max_steps <= 0
                ):
            raise ValueError('Etat ou objectif invalide')
        all_runes={r for names in RUNE_CHOICES.values() for r in names}
        stock=None if stock is None else dict(stock)
        if stock is not None and any(r not in all_runes or type(n) is not int or n<0 for r,n in stock.items()):
            raise ValueError('Stock invalide')
        if type(allow_preparatory) is not bool:raise ValueError('Option préparatoire invalide')
        self.allow_preparatory=allow_preparatory
        if transition_model is not None and not callable(transition_model):raise ValueError('Modèle de transition invalide')
        self.transition_model=transition_model
        self.level=level;self.targets=dict(targets)
        self.confidence=confidence;self.max_steps=max_steps
        # Deprecated monetary inputs are ignored, including saved legacy values.
        self._initial=(deepcopy(lines),float(pool),stock)
        self.reset(seed=seed)

    def reset(self, *, seed=None):
        self.lines,self.pool,self.stock=deepcopy(self._initial)
        self.rng=Random(seed);self.steps=0;self.closed=False
        return self.get_state()

    def _complete(self, state):
        return all(state['stats'].get(s,{}).get('value',0)>=v for s,v in self.targets.items())

    def get_state(self):
        stats={x['stat']:{'value':x['value'],'min':x.get('min'),'max':x.get('max'),
                            'target':self.targets.get(x['stat'])} for x in self.lines}
        vector=[];features=[]
        # Fixed stat vocabulary, with masks to distinguish absent/unknown from zero.
        for stat in STATS:
            line=stats.get(stat,{});lo=line.get('min');hi=line.get('max')
            scale=max(1,abs(lo or 0),abs(hi or 0),abs(self.targets.get(stat,0)))
            values=(int(stat in stats),line.get('value',0)/scale,
                    (lo or 0)/scale,(hi or 0)/scale,int(hi is not None),
                    self.targets.get(stat,0)/scale,int(stat in self.targets))
            for name,value in zip(('present','current','min','max','bounded','target','targeted'),values):
                features.append(f'{stat}:{name}');vector.append(value)
        features.extend(('pool','level','confidence','steps_remaining'))
        vector.extend((self.pool/100,self.level/200,self.confidence,
                       max(0,self.max_steps-self.steps)/self.max_steps))
        return {'schema':STATE_VERSION,'model_version':MODEL_VERSION,'stats':stats,
                **({'reasoning_version':'fm-reasoning-1','preparatory':True} if self.allow_preparatory else {}),
                'pool':self.pool,'confidence':self.confidence,'stock':deepcopy(self.stock),
                'features':tuple(features),'vector':tuple(vector)}

    def _spec(self, rune):
        stat=next(s for s,rs in RUNE_CHOICES.items() if rune in rs)
        ref=reference(rune)
        return {'stat':stat,'gain':ref.gain,'weight':ref.weight}

    def get_valid_actions(self):
        if self.closed:return []
        # Action legality needs current values only, not the wide learning vector.
        values={line['stat']:line['value'] for line in self.lines}
        maxima={line['stat']:line.get('max') for line in self.lines}
        if all(values.get(stat,0)>=target for stat,target in self.targets.items()):return ['stop']
        actions=[]
        for stat,target in sorted(self.targets.items()):
            current=values.get(stat,0)
            if current>=target:continue
            for rune in RUNE_CHOICES.get(stat,()):
                spec=self._spec(rune)
                # Targets are minima, as in copilote candidates(). A natural
                # surplus is legal; over/exo still needs an explicit target.
                maximum=maxima.get(stat)
                smallest=min(self._spec(r)['gain'] for r in RUNE_CHOICES.get(stat,()))
                minimal_finish=(maximum is not None and current<target<=maximum
                                and target-current<smallest and spec['gain']==smallest)
                finish_over=(maximum is not None and current<target==maximum<current+spec['gain']
                             and stat in ('Vitalité','Force','Intelligence','Chance','Agilité','Sagesse')
                             and (spec['weight']<=self.pool or rune.startswith('Pa ')
                                  and stat in ('Force','Intelligence','Chance','Agilité')
                                  and current>=max(20,.9*maximum)))
                if (maximum is not None and target<=maximum<current+spec['gain']
                        and not (minimal_finish or finish_over)):
                    continue
                if self.stock is not None and self.stock.get(rune,0)<=0:continue
                if not odds(self.lines,spec,level=self.level).get('blocked'):actions.append(rune)
        if self.allow_preparatory:
            from forgely_reasoning import strategic_options
            maxima={s:v for s,v in maxima.items() if v is not None}
            for option in strategic_options(values,self.targets,maxima,self.pool):
                rune=option['rune']
                if (not option['experimental'] or rune in actions
                        or (self.stock is not None and self.stock.get(rune,0)<=0)):continue
                if not odds(self.lines,self._spec(rune),level=self.level).get('blocked'):actions.append(rune)
        return actions+['stop']

    def reward(self, before, after, *, cost, failed=False):
        """Undiscounted potential shaping; only the entire jet earns success.

        Potential is in (0, .1], so even large partial gains cannot substitute
        for the terminal success bonus. Failed episodes end at zero potential:
        cycling or abandoning cannot retain accumulated shaping rewards.
        Monetary inputs are ignored; the complete target is the only objective.
        """
        def deficit(state):
            return sum(max(0,target-state['stats'].get(stat,{}).get('value',0))*WEIGHT_PER_POINT[stat]
                       for stat,target in self.targets.items())
        potential_before=.1/(1+deficit(before))
        potential_after=0. if failed else .1/(1+deficit(after))
        bonus=1. if not self._complete(before) and self._complete(after) and not failed else 0.
        return bonus+potential_after-potential_before

    def _attempt(self, action):
        return (self.transition_model or attempt)(self.lines,self._spec(action),self.pool,level=self.level,rng=self.rng)

    def step(self, action):
        if action not in self.get_valid_actions():raise ValueError('Action indisponible')
        before=self.get_state()
        info={'source':'simulation','real_observation':False,
              'model_version':MODEL_VERSION,'reward_version':REWARD_VERSION,'action':action}
        if action=='stop':
            self.closed=True
            reward=0. if self._complete(before) else self.reward(before,before,cost=0,failed=True)
            return before,reward,True,False,info
        result=self._attempt(action)
        self.lines=result['lines'];self.pool=result['pool'];self.steps+=1
        if self.stock is not None:self.stock[action]-=1
        after=self.get_state();terminated=self._complete(after)
        truncated=self.steps>=self.max_steps and not terminated
        self.closed=terminated or truncated
        info.update(outcome=result['outcome'],
                    changes=result['changes'],odds=result['odds'])
        return after,self.reward(before,after,cost=0,failed=truncated),terminated,truncated,info
