"""Synthetic comparison only. Run from project root; never promotes a policy."""
import importlib.util
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'Application'))
out=Path(__file__).resolve().parent
before='--before' in sys.argv
if before:
    spec=importlib.util.spec_from_file_location('forgely_training',out/'forgely_training.before.py')
    module=importlib.util.module_from_spec(spec)
    sys.modules['forgely_training']=module
    spec.loader.exec_module(module)
from forgely_training import TrainingConfig, run_training
from auditer_politique import audit_policy
label='before' if before else 'after'
targets={'Vitalité':300,'Force':40,'Intelligence':40,'Agilité':40,'Initiative':300,
         'Dommages Neutre':10,'Dommages Terre':10,'Dommages Feu':0,'Dommages Air':0,
         '% Résistance Eau':0,'Tacle':0}
result=run_training(TrainingConfig(14092,targets,episodes=100,max_steps=130,
                    evaluation_episodes=200,resume=False),out/label)
policy=out/label/result['run_id']/'policy.json'
audits=[audit_policy(policy,episodes=200,seed=seed) for seed in (314159,271828)]
(out/(label+'-benchmark.json')).write_text(json.dumps(dict(training=result,audits=audits),
    ensure_ascii=False,indent=2),encoding='utf-8')
print(label,[(a['seed'],a['evaluation']) for a in audits],flush=True)
