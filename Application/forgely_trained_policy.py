"""Bounded JSON policy loading, used only by the simulation background thread.

Learned values adjust a simulated ranking. They are never player observations
or probabilities and incompatible or unseen states supply no adjustment.
"""
import json
from pathlib import Path
import sys
from time import monotonic

from forgely_dofocus_engine import MODEL_VERSION
from forgely_dofocus import RUNE_CHOICES,WEIGHT_PER_POINT
from forgely_rl import REWARD_VERSION
from forgely_rules import finite_number
from forgely_general_policy import valid_policy


def training_directory():
    base=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent
    return base/'Entrainements'


class TrainedPolicies:
    def __init__(self,root=None):
        self.root=Path(root) if root is not None else training_directory()
        self._stamp=None;self._policies=[];self._last_scan=-float('inf')

    def refresh(self,*,force=False):
        """File IO belongs exclusively to the caller's background worker."""
        now=monotonic()
        if not force and now-self._last_scan<1:return False
        self._last_scan=now
        try:
            paths=sorted(self.root.glob('*/policy.json'),reverse=True)
            from forgely_training import selector_runtime_digest,selector_code_digest
            runtime=(selector_code_digest(),selector_runtime_digest())
            stamp=(runtime,tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in paths))
        except OSError:return False
        if stamp==self._stamp:return False
        self._stamp=stamp;champions={};loaded_bytes=0
        from forgely_training import POLICY_VERSION,advice_validation,policy_rank,policy_advice_validation
        all_actions={r for names in RUNE_CHOICES.values() for r in names}|{'stop'}
        for filename,_,size in stamp[1]:
            if not 0<size<=64*1024*1024:continue
            try:
                data=json.loads(Path(filename).read_text(encoding='utf-8'))
                config=data.get('configuration',{})
                if (data.get('model_version')!=MODEL_VERSION or data.get('reward_version')!=REWARD_VERSION
                    or data.get('policy_version')!=POLICY_VERSION or data.get('source')!='simulation'
                    or data.get('real_observations')!=0 or data.get('eligible_for_advice') is not True
                    or (data.get('general_policy') is not None and not valid_policy(data['general_policy']))
                    or not policy_advice_validation(data,selector_identity=runtime)['eligible']
                    or not isinstance(config,dict) or config.get('prices') or config.get('budget') is not None
                    or config.get('allow_preparatory',False) is not False
                    or type(data.get('episodes_total')) is not int or data['episodes_total']<1
                    or type(config.get('max_steps')) is not int or not 1<=config['max_steps']<=5000
                    or not isinstance(data.get('q'),dict) or len(data['q'])>50000
                    or not isinstance(data.get('visits'),dict) or len(data['visits'])>50000
                    or not isinstance(data.get('profile_lines'),list) or not 1<=len(data['profile_lines'])<=64):continue
                if any(not isinstance(k,str) or len(k)>1024 or not isinstance(row,dict)
                       or any(a not in all_actions or not finite_number(v) or abs(v)>1e12
                              for a,v in row.items()) for k,row in data['q'].items()):continue
                if any(not isinstance(k,str) or len(k)>1024 or not isinstance(row,dict)
                       or any(a not in all_actions or type(v) is not int or not 0<=v<=10**12
                              for a,v in row.items()) for k,row in data['visits'].items()):continue
                profile=data['profile_lines']
                if any(not isinstance(x,dict) or x.get('stat') not in WEIGHT_PER_POINT
                       or x.get('weight')!=WEIGHT_PER_POINT[x['stat']]
                       or any(x.get(k) is not None and not finite_number(x[k]) for k in ('min','max'))
                       for x in profile):continue
                if len({x['stat'] for x in profile})!=len(profile):continue
                data['_run_id']=Path(filename).parent.name
                # Keep the best compatible archive BEFORE applying memory limits.
                # Newer inferior copies must not crowd out an older champion.
                group=json.dumps([config['item_id'],config.get('targets'),config['max_steps'],config.get('empirical_revision'),
                    sorted((x['stat'],x.get('min'),x.get('max'),x.get('weight')) for x in profile)],
                    sort_keys=True,ensure_ascii=False)
                previous=champions.get(group)
                if previous is not None and policy_rank(previous)>=policy_rank(data):continue
                if previous is not None:loaded_bytes-=previous['_file_bytes']
                data['_file_bytes']=size;champions[group]=data;loaded_bytes+=size
                while loaded_bytes>64*1024*1024:
                    worst=min(champions,key=lambda k:policy_rank(champions[k]))
                    loaded_bytes-=champions.pop(worst)['_file_bytes']

            except (OSError,ValueError,TypeError,AttributeError,KeyError):continue
        self._policies=sorted(champions.values(),key=policy_rank,reverse=True)
        return True

    def factors(self,context):
        """In-memory lookup; no file scans or live state mutations."""
        from forgely_training import action_values,state_key
        goals=dict(context.targets)
        lines=context._lines()
        for policy in self._policies:
            config=policy['configuration']
            empirical=getattr(context,'empirical',None)
            revision=empirical.digest if empirical is not None and empirical.sample_count else None
            if revision!=config.get('empirical_revision'):continue
            if config.get('item_id')!=context.key[1] or config.get('targets')!=goals:continue
            profile=policy['profile_lines']
            def signature(rows):
                return sorted((x['stat'],x.get('min'),x.get('max'),x.get('weight')) for x in rows)
            if signature(profile)!=signature(lines):continue
            env=context.environment(max_steps=config['max_steps'])
            # An audit without live OCR/neighbour corrections cannot authorize
            # a selector using them. Only exact, frozen qualified records for
            # every available action can prove equivalent live source inputs.
            worker=getattr(context,'worker',None)
            real_for=getattr(worker,'real_for',None)
            experience_for=getattr(worker,'experience_for',None)
            if real_for or experience_for:
                if empirical is None or real_for is None:continue
                from forgely_video_store import item_profile
                equipment,_=item_profile(config['item_id'])
                if equipment is None:continue
                comparable=True
                jet={x['stat']:x['value'] for x in lines}
                for rune in env.get_valid_actions():
                    if rune=='stop':continue
                    frozen=empirical.observation(config['item_id'],rune,jet,env.pool)
                    actual=real_for(equipment.identity_name,rune,jet,env.pool)
                    if (not frozen or not frozen.get('usable') or not actual or actual.get('verified') is not True
                            or actual.get('quality')!='local_verified' or actual.get('n')!=frozen['n']
                            or actual.get('counts')!=frozen['counts']):
                        comparable=False;break
                if not comparable:continue
            state=env.get_state()
            try:
                generalized=valid_policy(policy.get('general_policy'))
                values=action_values(policy,state)
                visits=policy['visits'].get(state_key(state),{})
                valid=set(env.get_valid_actions())
                row={a:v for a,v in values.items() if a in valid and finite_number(v)
                     and (generalized or type(visits.get(a)) is int and visits[a]>0)}
            except (KeyError,TypeError,ValueError,AttributeError):continue
            if len(row)<2:continue
            low=min(row.values());high=max(row.values())
            if high-low<1e-9:continue
            return {a:{'factor':min(1.2,max(.8,.8+.4*(v-low)/(high-low))),
                'kind':'trained_simulation_policy','source':'simulation','real_observations':0,
                'run_id':policy['_run_id'],'episodes':policy['episodes_total'],
                'action_visits':visits.get(a,0),'state_visits':sum(visits.get(a,0) for a in row),
                'generalized':generalized,
                'search_episodes':policy['general_policy']['episodes'] if generalized else 0,
                'stop_preferred':row.get('stop',-float('inf'))==high,
                'is_game_probability':False} for a,v in row.items() if a!='stop'}
        return {}
