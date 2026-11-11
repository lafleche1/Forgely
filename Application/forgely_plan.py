"""Local, transparent planning assistant. Not official DOFUS odds; never controls game."""
from __future__ import annotations
import json, os
from pathlib import Path

PLAN_PATH = Path(os.getenv('LOCALAPPDATA') or Path.home()) / 'Forgely' / 'objectifs.json'
# Names represent player-visible characteristics; rune mapping is a *suggestion*, not odds.
from forgely_rules import RUNE_CHOICES
STATS = {stat:tuple(runes) for stat,runes in RUNE_CHOICES.items()}


def save_plan(item, values, path=PLAN_PATH, *, item_id=None, level=None):
    item = item.strip()
    if not item or len(item)>100:
        raise ValueError('Indique le nom de l’équipement (100 caractères maximum).')
    if level is not None and (type(level) is not int or not 1<=level<=200):
        raise ValueError('Le niveau doit être un entier entre 1 et 200, ou rester vide.')
    clean={}
    for name,pair in values.items():
        if name not in STATS: raise ValueError('Statistique inconnue : '+name)
        current,target=pair
        if target is None: continue
        if current is not None and (type(current) is not int or current< -20000 or current>20000): raise ValueError('Jet actuel invalide')
        if type(target) is not int or target< -20000 or target>20000: raise ValueError('Objectif invalide')
        clean[name]={'current':current,'target':target}
    if not clean: raise ValueError('Renseigne au moins une caractéristique cible.')
    data={'item':item,'stats':clean}
    if level is not None:data['level']=level
    if item_id is not None:
        if type(item_id) is not int or item_id<=0:raise ValueError('Identifiant d’objet invalide')
        data['item_id']=item_id
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return data

def load_plan(path=PLAN_PATH):
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data,dict) or not isinstance(data.get('stats'),dict): return None
        return data
    except (OSError, ValueError, TypeError): return None

def next_action(plan, pool=None):
    """Same source-aware engine as the detailed advice; no implicit zero pool."""
    if not plan:return ('Aucun objectif','Choisis un équipement et définis son jet cible.')
    if any(v.get('current') is None for v in plan['stats'].values()):
        return ('Jet à lire','Il faut confirmer les valeurs actuelles avant de proposer une rune.')
    from forgely_decision import advise
    proposal=advise({s:v['current'] for s,v in plan['stats'].items()},
                    {s:v['target'] for s,v in plan['stats'].items()},pool=pool,item=plan.get('item'),level=plan.get('level'))
    return proposal.summary,proposal.explanation
