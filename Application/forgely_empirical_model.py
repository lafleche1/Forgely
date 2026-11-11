"""Frozen exact-context empirical kernel, shared by advice and training.

Only qualified real transitions enter. Simulated continuations are query states,
never new evidence. Loss resampling is conditional on the drawn outcome.
"""
from collections import defaultdict, Counter
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from math import floor
from pathlib import Path
from random import Random
import sqlite3

from forgely_dofocus import RUNE_CHOICES, reference, WEIGHT_PER_POINT
from forgely_dofocus_engine import odds, attempt, MODEL_VERSION
from forgely_fm_model import MIN_REAL, PRIOR_STRENGTH, calibrate_prediction
from forgely_video_store import catalogue, item_profile, qualify_event, qualified_video_rows, atomic_json
from forgely_equipment_catalog import equipment_bounds
from forgely_items import key_for

MIN_OUTCOME_LOSSES=5
SPECS={(s,reference(r).gain,reference(r).weight):r for s,rs in RUNE_CHOICES.items() for r in rs}


def resolve_item(value):
    if type(value) is int:return value
    if not isinstance(value,str):return None
    found=[i.item_id for i in catalogue().items if key_for(i.identity_name)==key_for(value)]
    return found[0] if len(found)==1 else None


def _profile_key(item_id):
    item,_=item_profile(item_id)
    if item is None:return None
    return tuple(sorted((s,lo,hi,WEIGHT_PER_POINT.get(s)) for s,(lo,hi) in equipment_bounds(item).items()))


def _line_key(lines):
    return tuple(sorted((x['stat'],x.get('min'),x.get('max'),x['weight']) for x in lines if x.get('max') is not None))


class EmpiricalModel:
    def __init__(self,records=()):
        accepted=[];self._groups=defaultdict(list)
        for original in records:
            try:
                e=deepcopy(original)
                if e.get('source') not in ('video_verified','local_screen_verified') or not qualify_event(e)['eligible']:continue
                profile=_profile_key(e['item_id'])
                if e.get('profile_key') is not None and tuple(map(tuple,e['profile_key']))!=profile:continue
                e['profile_key']=profile
                key=(e['item_id'],e['rune'],tuple(sorted(e['before']['jet'].items())),float(e['before']['pool']),profile)
                self._groups[key].append(e);accepted.append(e)
            except (ValueError,TypeError,KeyError):continue
        self._records=tuple(sorted(accepted,key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False)))
        for group in self._groups.values():group.sort(key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False))
        self._per_item={}
        self.digest=hashlib.sha256(json.dumps(self._records,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        self.sample_count=len(self._records)

    def for_item(self,item_id):
        item_id=resolve_item(item_id)
        if item_id not in self._per_item:
            self._per_item[item_id]=EmpiricalModel(e for e in self._records if e['item_id']==item_id)
        return self._per_item[item_id]

    def observation(self,item_id,rune,jet,pool):
        item_id=resolve_item(item_id);item,profile=item_profile(item_id)
        if item is None or not isinstance(jet,dict) or not set(profile)<=jet.keys():return None
        bounds=equipment_bounds(item)
        lines=[dict(stat=s,value=value,min=bounds[s][0] if s in bounds else None,
                    max=bounds[s][1] if s in bounds else None,weight=WEIGHT_PER_POINT.get(s)) for s,value in jet.items()]
        ref=reference(rune);stat=next((s for s,rs in RUNE_CHOICES.items() if rune in rs),None)
        if stat is None:return None
        counts=Counter(e['outcome'] for e in self._samples(item_id,lines,{'stat':stat,'gain':ref.gain,'weight':ref.weight},pool))
        if not counts:return None
        return {'verified':True,'counts':dict(counts),'n':sum(counts.values()),'quality':'local_verified','usable':sum(counts.values())>=MIN_REAL}

    def _samples(self,item_id,lines,spec,pool):
        item_id=resolve_item(item_id)
        rune=SPECS.get((spec['stat'],spec['gain'],spec['weight']))
        if item_id is None or rune is None:return ()
        key=(item_id,rune,tuple(sorted((x['stat'],x['value']) for x in lines)),float(pool),_line_key(lines))
        return self._groups.get(key,())

    def probabilities(self,item_id,lines,spec,pool,*,level=200):
        base=odds(lines,spec,level=level)
        if base.get('blocked'):return base
        samples=self._samples(item_id,lines,spec,pool)
        counts=Counter(e['outcome'] for e in samples)
        prediction={k:base[k.lower()] for k in ('SC','SN','EC')}
        calibrated=calibrate_prediction(prediction,{'verified':True,'counts':dict(counts)})
        if len(samples)<MIN_REAL:return base
        return {**base,**{k.lower():calibrated[k] for k in ('SC','SN','EC')},
                **{k:calibrated[k] for k in ('SC','SN','EC')},
                'empirical_n':len(samples),'empirical_weight':len(samples)/(PRIOR_STRENGTH+len(samples)),
                'calibration_n':len(samples),'real_weight':len(samples)/(PRIOR_STRENGTH+len(samples)),
                'evidence_revision':self.digest,'empirical_source':'qualified_real_exact'}

    def attempt(self,item_id,lines,spec,pool,*,level=200,rng=None,probabilities=None):
        generator=rng or Random()
        rates=probabilities or self.probabilities(item_id,lines,spec,pool,level=level)
        if rates.get('blocked'):return attempt(lines,spec,pool,level=level,rng=generator)
        samples=self._samples(item_id,lines,spec,pool)
        if len(samples)<MIN_REAL:
            return attempt(lines,spec,pool,level=level,rng=generator,probabilities=probabilities)
        draw=generator.random()*100
        outcome='SC' if draw<rates['sc'] else 'SN' if draw<rates['sc']+rates['sn'] else 'EC'
        conditional=[e for e in samples if e['outcome']==outcome]
        alpha=len(samples)/(PRIOR_STRENGTH+len(samples))
        if (len(samples)>=MIN_REAL and len(conditional)>=MIN_OUTCOME_LOSSES
                and generator.random()<alpha):
            event=conditional[min(len(conditional)-1,floor(generator.random()*len(conditional)))]
            after=event['after'];result=deepcopy(lines)
            present={x['stat'] for x in result}
            for stat,value in after['jet'].items():
                if stat not in present:
                    result.append(dict(stat=stat,value=0,min=None,max=None,weight=WEIGHT_PER_POINT[stat]))
            changes={}
            before={x['stat']:x['value'] for x in lines}
            for line in result:
                value=after['jet'][line['stat']]
                delta=value-before.get(line['stat'],0)
                if delta:changes[line['stat']]=delta
                line['value']=value
            return dict(lines=result,pool=after['pool'],pool_delta=after['pool']-pool,outcome=outcome,
                        odds=rates,changes=changes,empirical_loss_sampled=True,evidence_revision=self.digest)
        # The outcome is fixed here; only fallback loss allocation remains random.
        result=attempt(lines,spec,pool,level=level,rng=generator,
                       probabilities={k:100. if k==outcome.lower() else 0. for k in ('sc','sn','ec')})
        result['odds']=rates;result['empirical_loss_sampled']=False
        return result

    def transition(self,item_id):
        return lambda lines,spec,pool,**kw:self.attempt(item_id,lines,spec,pool,**kw)

    def save(self,path):
        atomic_json(path,{'version':MODEL_VERSION,'digest':self.digest,'records':self._records})

    @classmethod
    def load(cls,path):
        raw=json.loads(Path(path).read_text(encoding='utf8'))
        if raw.get('version')!=MODEL_VERSION:raise ValueError('Instantané de modèle réel incompatible')
        model=cls(raw['records'])
        if model.digest!=raw.get('digest'):raise ValueError('Instantané de données réelles altéré ou profil modifié')
        return model


def load_empirical_model(db_file):
    path=Path(db_file)
    if not path.is_file():return EmpiricalModel()
    records=[]
    for video_id,event_id,event in qualified_video_rows(path):
        records.append({**event,'source':'video_verified','evidence_id':f'{video_id}:{event_id}'})
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
        columns={x[1] for x in db.execute('PRAGMA table_info(fusion_contexts)')}
        if {'item','rune','outcome','before_json','after_json','calibration_verified','source'}<=columns:
            rows=db.execute("SELECT rowid,item,rune,outcome,before_json,after_json FROM fusion_contexts WHERE source='local_screen' AND calibration_verified=1")
            for ident,item,rune,outcome,before,after in rows:
                try:
                    item_id=resolve_item(item);_,profile=item_profile(item_id)
                    if not profile:continue
                    records.append(dict(id=f'screen:{ident}',item_id=item_id,rune=rune,outcome=outcome,
                        before=json.loads(before),after=json.loads(after),natural_max=profile,
                        event_confirmed=True,stable=True,issues=[],status='candidate',source='local_screen_verified',
                        evidence={'before':f'qualified-context:{ident}:before','after':f'qualified-context:{ident}:after'}))
                except (ValueError,TypeError):continue
    return EmpiricalModel(records)
