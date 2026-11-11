"""Reproducible pilot experiment; not loaded automatically by live advice."""
import sys,json,time,math,hashlib
from pathlib import Path
from random import Random
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'Application'/'forgely_rl.py').is_file())
sys.path.insert(0,str(ROOT/'Application'))
from forgely_rl import ForgemagingEnv,STATE_VERSION,REWARD_VERSION
from forgely_dofocus_engine import MODEL_VERSION
from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
from forgely_dofocus import canonical_stat,WEIGHT_PER_POINT,RUNE_CHOICES,reference

OUT=ROOT/'Application'/'assets'/'training'/'pilot-20261107'
OUT.mkdir(parents=True,exist_ok=True)
item=EquipmentCatalog().get(14092)
bounds={canonical_stat(s):pair for s,pair in equipment_bounds(item).items()}
lines=[dict(stat=s,value=math.floor((a+b)/2+.5),min=a,max=b,weight=WEIGHT_PER_POINT[s])
       for s,(a,b) in sorted(bounds.items())]
targets={'Force':40,'Intelligence':40}
env=ForgemagingEnv(lines,10.,targets,level=item.level,max_steps=30)
q={};visits={};rng=Random(20261107)

def key(state):
    # Aggregation keeps the pilot table small; it is an approximation, not a full Markov state.
    stats=state['stats']
    quality=sum(max(0,x['value'])*WEIGHT_PER_POINT[s] for s,x in stats.items())
    return str((stats['Force']['value'],stats['Intelligence']['value'],
                int(state['pool']//5),int(quality//20),
                int(state['vector'][-1]*30)//5))

def choose(state,actions,explore=0):
    if rng.random()<explore:return rng.choice(actions)
    values=q.get(key(state),{})
    best=max(values.get(a,0.) for a in actions)
    return rng.choice([a for a in actions if values.get(a,0.)==best])

started=time.perf_counter();transitions=0;training_success=0
for episode in range(3000):
    state=env.reset(seed=10000+episode)
    while True:
        actions=env.get_valid_actions()
        action=choose(state,actions,.35-.30*episode/2999)
        new,reward,done,truncated,info=env.step(action)
        k=key(state);table=q.setdefault(k,{})
        future=0 if done or truncated else max(q.get(key(new),{}).get(a,0.) for a in env.get_valid_actions())
        count=visits.setdefault(k,{});count[action]=count.get(action,0)+1
        alpha=max(.05,1/(count[action]**.6))
        table[action]=table.get(action,0.)+alpha*(reward+.97*future-table.get(action,0.))
        transitions+=int(action!='stop');state=new
        if done or truncated:
            training_success+=int(all(state['stats'][s]['value']>=v for s,v in targets.items()))
            break
    if (episode+1)%500==0:print(f'training {episode+1}/3000; transitions={transitions}',flush=True)

def evaluate(policy):
    total=steps=success=stops=truncations=0;counts={'SC':0,'SN':0,'EC':0}
    for episode in range(500):
        state=env.reset(seed=1000000+episode)
        while True:
            actions=env.get_valid_actions()
            runes=[a for a in actions if a!='stop']
            if policy=='learned':action=choose(state,actions)
            elif not runes:action='stop'
            elif policy=='random':action=rng.choice(runes)
            else:
                stat=max(targets,key=lambda s:targets[s]-state['stats'][s]['value'])
                choices=[a for a in runes if a in RUNE_CHOICES[stat]] or runes
                action=min(choices,key=lambda a:reference(a).gain)
            state,reward,done,truncated,info=env.step(action)
            total+=reward;steps+=int(action!='stop')
            if info.get('outcome'):counts[info['outcome']]+=1
            if done or truncated:
                success+=int(all(state['stats'][s]['value']>=v for s,v in targets.items()))
                stops+=int(action=='stop');truncations+=int(truncated)
                break
    return dict(episodes=500,successes=success,success_rate=success/500,
                mean_reward=total/500,mean_attempts=steps/500,stops=stops,
                truncated=truncations,outcomes=counts,source='simulation',real_observations=0)

metrics={p:evaluate(p) for p in ('learned','small_rune','random')}
report=dict(item_id=item.item_id,item=item.name,level=item.level,initial_lines=lines,
            initial_pool=10,targets=targets,horizon=30,training_episodes=3000,
            training_rune_attempts=transitions,training_successes=training_success,
            learned_states=len(q),seed=20261107,algorithm='tabular Q-learning with aggregated states',
            discount=.97,model_version=MODEL_VERSION,state_version=STATE_VERSION,
            reward_version=REWARD_VERSION,evaluation=metrics,prices_provided=False,
            limitations=['One fixed starting item and jet; no generalization claim.',
                         'Aggregated state loses detail; no full Markov guarantee.',
                         'Simulator results, not observed game success rates.',
                         'No rune prices; not an economic optimization.',
                         'Saved experimental policy is not enabled in live advice.'],
            duration_seconds=round(time.perf_counter()-started,2))
(OUT/'metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'policy.json').write_text(json.dumps(dict(metadata=report,q=q,visits=visits),ensure_ascii=False),encoding='utf-8')
import shutil
shutil.copy2(__file__,OUT/'reproduce.py')
print(json.dumps(report,ensure_ascii=True),flush=True)
