"""Fast offline odds plus bounded virtual trials on a dedicated latest-job worker.

All outputs remain simulations. This module has no observation database access.
"""
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass, replace
from functools import lru_cache
from hashlib import sha256
from random import Random
import threading
from forgely_dofocus import normalise_jet,canonical_stat,reference,RUNE_CHOICES,WEIGHT_PER_POINT
from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
from forgely_items import key_for
from forgely_rules import finite_number
from forgely_dofocus_engine import odds,attempt,MODEL_VERSION
from forgely_rl import ForgemagingEnv, REWARD_VERSION
from forgely_trained_policy import TrainedPolicies
from forgely_sequence import plan_sequences, calibrated_probabilities, options as sequence_options, validate_choice


@lru_cache(maxsize=1)
def _equipment():
    return {key_for(x.identity_name):x for x in EquipmentCatalog().items}


@lru_cache(maxsize=128)
def _profile(name):
    item=_equipment().get(key_for(name))
    if item is None:return None
    bounds={canonical_stat(s):pair for s,pair in equipment_bounds(item).items()}
    if not bounds or any(s not in WEIGHT_PER_POINT for s in bounds):return None
    return item,bounds


@dataclass(frozen=True)
class SimulationContext:
    worker: object
    key: tuple
    level: int
    lines: tuple
    pool: float
    targets: tuple

    def _lines(self):
        return [dict(zip(('stat','value','min','max','weight'),row)) for row in self.lines]

    def environment(self, **options):
        """Independent episode: training cannot mutate the live observation."""
        return ForgemagingEnv(self._lines(),self.pool,dict(self.targets),level=self.level,**options)

    def evidence(self,rune):
        ref=reference(rune)
        stat=next((s for s,names in RUNE_CHOICES.items() if rune in names),None)
        if stat is None or ref.gain is None or ref.weight is None:return None
        result=odds(self._lines(),{'stat':stat,'gain':ref.gain,'weight':ref.weight},level=self.level)
        common={'kind':'local_dofocus_model','model_version':MODEL_VERSION,
            'real_observation':False,'weight':ref.weight,'url':'https://dofocus.fr/forgemagie/'}
        if result.get('blocked'):
            return {**common,'blocked':True,'line_max':result['limit'],'reason':result['blocked']}
        probabilities={k.upper():result[k] for k in ('sc','sn','ec')}
        output={**common,'blocked':False,'probabilities':probabilities,
            'display':{k:format(v,'.10f').rstrip('0').rstrip('.') for k,v in probabilities.items()},
            'regime':result['regime'],'estimated':bool(result.get('estimated',False))}
        with self.worker._condition:
            outlook=self.worker._cache.get(self.key,{}).get(rune)
            if outlook is not None:
                output['outlook']=deepcopy(outlook)
                if outlook.get('sequence'):
                    output['sequence']=deepcopy(outlook['sequence'])
                if outlook.get('trained_policy'):
                    output['trained_policy']=deepcopy(outlook['trained_policy'])
        return output


class SimulationWorker:
    def __init__(self,*,trials=48,on_ready=None,max_states=8,training_root=None,real_for=None,experience_for=None):
        if type(trials) is not int or not 16<=trials<=256:raise ValueError('Nombre d’essais invalide')
        if type(max_states) is not int or not 1<=max_states<=32:raise ValueError('Cache invalide')
        self.experience_for=experience_for
        self.real_for=real_for
        self.trials=trials;self.on_ready=on_ready;self.max_states=max_states
        self._condition=threading.Condition();self._cache=OrderedDict()
        self._pending=None;self._latest=None;self._thread=None;self._stopped=False
        self._latest_context=None;self._policies=TrainedPolicies(training_root)
        self.last_error=None

    @staticmethod
    def item_id(item):
        equipment=_equipment().get(key_for(item))
        return equipment.item_id if equipment else None

    def results_for(self,key):
        with self._condition:return deepcopy(self._cache.get(key))

    def context(self,item,jet,pool,targets,*,revision=0):
        profile=_profile(item)
        jets=normalise_jet(jet);goals=normalise_jet(targets)
        if (profile is None or not jets or not goals or not finite_number(pool,nonnegative=True)
                or pool>30000 or not set(goals).issubset(jets)):return None
        equipment,bounds=profile
        if (not set(bounds).issubset(jets) or any(s not in WEIGHT_PER_POINT for s in jets)
                or len(jets)>64 or any(abs(v)>30000 for v in jets.values())
                or not 1<=equipment.level<=200):return None
        lines=tuple((s,value,*(bounds[s] if s in bounds else (None,None)),WEIGHT_PER_POINT[s])
            for s,value in sorted(jets.items()))
        key=(MODEL_VERSION,equipment.item_id,equipment.level,lines,float(pool),tuple(sorted(goals.items())),revision)
        context=SimulationContext(self,key,equipment.level,lines,float(pool),tuple(sorted(goals.items())))
        with self._condition:
            if self._stopped:return None
            if key!=self._latest:
                self._latest=key
                self._latest_context=context
                if key not in self._cache:self._pending=context
                self._condition.notify_all()
            if self._thread is None:
                self._thread=threading.Thread(target=self._run,name='Forgely-Simulateur',daemon=True)
                self._thread.start()
        return context

    @staticmethod
    def _deficit(jet,targets):
        return sum(max(0,target-jet[stat])*WEIGHT_PER_POINT[stat] for stat,target in targets)

    def _simulate(self,context):
        self._policies.refresh()
        trained=self._policies.factors(context)
        lines=context._lines();before={x['stat']:x['value'] for x in lines}
        environment=context.environment()
        reward_before={'stats':{x['stat']:{'value':x['value']} for x in lines}}
        baseline=self._deficit(before,context.targets)
        results={}
        runes=dict.fromkeys(r for stat,target in context.targets if before[stat]<target
                           for r in RUNE_CHOICES.get(stat,()))
        for rune in runes:
            with self._condition:
                if self._stopped or context.key!=self._latest:return None
            ref=reference(rune)
            stat=next(s for s,names in RUNE_CHOICES.items() if rune in names)
            spec={'stat':stat,'gain':ref.gain,'weight':ref.weight}
            if odds(lines,spec,level=context.level).get('blocked'):continue
            seed=int.from_bytes(sha256(repr((context.key,rune)).encode('utf-8')).digest()[:8],'big')
            rng=Random(seed);loss=progress=remaining=reward=0.;counts={o:0 for o in ('SC','SN','EC')}
            for _ in range(self.trials):
                result=attempt(lines,spec,context.pool,level=context.level,rng=rng)
                counts[result['outcome']]+=1
                after={x['stat']:x['value'] for x in result['lines']}
                deficit=self._deficit(after,context.targets)
                loss+=max(0,deficit-baseline);progress+=baseline-deficit;remaining+=result['pool']
                reward+=environment.reward(reward_before,
                    {'stats':{s:{'value':v} for s,v in after.items()}},cost=0)
            results[rune]={'trials':self.trials,'mean_target_loss':loss/self.trials,
                'mean_progress':progress/self.trials,'mean_pool':remaining/self.trials,
                'counts':counts,'real_observations':0,'kind':'virtual_trials',
                'mean_reward':reward/self.trials,'reward_version':REWARD_VERSION}
            if rune in trained:results[rune]['trained_policy']=trained[rune]
        def cancelled():
            with self._condition:
                return self._stopped or context.key!=self._latest
        seed=int.from_bytes(sha256(repr(context.key).encode('utf8')).digest()[:8],'big')
        calibration={}
        item=next((x for x in _equipment().values() if x.item_id==context.key[1]),None)
        records={}
        def real_for(rune):
            if rune not in records:
                records[rune]=self.real_for(item.identity_name,rune,before,context.pool) if self.real_for and item else None
            return records[rune]
        if self.real_for:
            if item:
                for row in sequence_options(lines,context.pool,dict(context.targets),level=context.level):
                    rune=row[1];ref=reference(rune)
                    spec={'stat':row[2],'gain':ref.gain,'weight':ref.weight}
                    base=odds(lines,spec,level=context.level)
                    measured=real_for(rune)
                    adjusted=calibrated_probabilities(base,measured)
                    if adjusted:calibration[rune]=adjusted
        def continuation(current,pool,choices):
            virtual=replace(context,lines=tuple((x['stat'],x['value'],x.get('min'),x.get('max'),x['weight'])
                                                for x in current),pool=pool)
            learned=self._policies.factors(virtual)
            if not learned:return choices[0][1]
            return max(choices,key=lambda row:(row[0]*learned.get(row[1],{}).get('factor',1.),row[1]))[1]
        sequences=plan_sequences(lines,context.pool,dict(context.targets),level=context.level,
                                 seed=seed,trials=16,horizon=8,cancelled=cancelled,root_calibration=calibration,continuation=continuation)
        if sequences is None:return None
        if sequences:
            ordered=sorted((row['value'] for row in sequences.values()),reverse=True)
            uncertain=all(row['completed']==0 for row in sequences.values()) or (len(ordered)>1 and ordered[0]-ordered[1]<.02)
            if uncertain:
                sequences=plan_sequences(lines,context.pool,dict(context.targets),level=context.level,
                    seed=seed,trials=32,horizon=8,cancelled=cancelled,
                    root_calibration=calibration,continuation=continuation)
                if sequences is None:return None
            for sequence in sequences.values():sequence['focused_search']=uncertain
            from forgely_decision import candidates
            maxima={x['stat']:x['max'] for x in lines if x.get('max') is not None}
            experiences={}
            def experience_for(rune):
                if rune not in experiences:
                    experiences[rune]=self.experience_for(item.identity_name,rune,before,context.pool,dict(context.targets),maxima) if self.experience_for and item else None
                return experiences[rune]
            def evidence(rune,planned=False):
                row=context.evidence(rune)
                if row is None:return None
                row.pop('sequence',None)
                if rune in results:row['outlook']=results[rune]
                if rune in trained:row['trained_policy']=trained[rune]
                else:row.pop('trained_policy',None)
                if planned and rune in sequences:row['sequence']=sequences[rune]
                return row
            from forgely_pricing import active_price_book
            ranking_args=dict(natural_max=maxima,pool=context.pool,item=item.identity_name if item else None,
                              price_book=active_price_book(),
                              contextual_for=real_for,experience_for=experience_for)
            baseline_rows=candidates(before,dict(context.targets),simulation_for=evidence,**ranking_args)
            planned_rows=candidates(before,dict(context.targets),simulation_for=lambda r:evidence(r,True),**ranking_args)
            if not baseline_rows or not planned_rows:return results
            baseline=baseline_rows[0][1]
            selected=planned_rows[0][1]
            validation_runs=plan_sequences(lines,context.pool,dict(context.targets),level=context.level,
                seed=seed+10**12,trials=32,horizon=8,cancelled=cancelled,
                root_calibration=calibration,continuation=continuation)
            if validation_runs is None:return None
            validation=validate_choice(sequences,validation_runs,baseline,selected=selected)
            for sequence in sequences.values():sequence['validation']=validation
        for rune,sequence in sequences.items():
            if rune in results:results[rune]['sequence']=sequence
        return results

    def _run(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda:self._stopped or self._pending is not None,timeout=2)
                if self._stopped:return
                context=self._pending;self._pending=None
            try:
                if context is None:
                    # A completed desktop training can update a stationary jet.
                    if not self._policies.refresh():continue
                    with self._condition:context=self._latest_context
                    if context is None:continue
                results=self._simulate(context)
                with self._condition:
                    if results is None or self._stopped:continue
                    self._cache[context.key]=results;self._cache.move_to_end(context.key)
                    while len(self._cache)>self.max_states:self._cache.popitem(last=False)
                    current=context.key==self._latest;self.last_error=None
                if current and self.on_ready:self.on_ready(context.key)
            except (ValueError,KeyError,TypeError,OverflowError) as exc:
                self.last_error=str(exc)

    def stop(self):
        with self._condition:
            self._stopped=True;self._pending=None;self._condition.notify_all()
        if self._thread and self._thread.is_alive():self._thread.join(timeout=2)
