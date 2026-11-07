"""Local, transparent planning assistant. Not official DOFUS odds; never controls game."""
from __future__ import annotations
import json, os
from pathlib import Path

PLAN_PATH = Path(os.getenv('LOCALAPPDATA') or Path.home()) / 'Forgely' / 'objectifs.json'
# Names represent player-visible characteristics; rune mapping is a *suggestion*, not odds.
STATS = {
    'Vitalité': ('Vi','Pa Vi','Ra Vi'),
    'Force': ('Fo','Pa Fo','Ra Fo'),
    'Intelligence': ('Ine','Pa Ine','Ra Ine'),
    'Chance': ('Cha','Pa Cha','Ra Cha'),
    'Agilité': ('Age','Pa Age','Ra Age'),
    'Sagesse': ('Sa','Pa Sa','Ra Sa'),
    'Puissance': ('Pui','Pa Pui','Ra Pui'),
    'Initiative': ('Ini','Pa Ini','Ra Ini'),
    'Prospection': ('Prospe','Pa Prospe'),
    'Portée': ('Po',),
    'PA': ('Ga Pa',),
    'PM': ('Ga Pme',),
}

# Same catalogue as the actual advisory engine; OCR names remain selectable.
from forgely_rules import RUNE_CHOICES
STATS.update(RUNE_CHOICES)

def save_plan(item, values, path=PLAN_PATH):
    item = item.strip()
    if not item or len(item)>100:
        raise ValueError('Indique le nom de l’équipement (100 caractères maximum).')
    clean={}
    for name,pair in values.items():
        if name not in STATS: raise ValueError('Statistique inconnue : '+name)
        current,target=pair
        if target is None: continue
        if current is not None and (not isinstance(current,int) or current<0 or current>20000): raise ValueError('Jet actuel invalide')
        if not isinstance(target,int) or target<0 or target>20000: raise ValueError('Objectif invalide')
        clean[name]={'current':current,'target':target}
    if not clean: raise ValueError('Renseigne au moins une caractéristique cible.')
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'item':item,'stats':clean},ensure_ascii=False,indent=2),encoding='utf-8')
    return {'item':item,'stats':clean}

def load_plan(path=PLAN_PATH):
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data,dict) or not isinstance(data.get('stats'),dict): return None
        return data
    except (OSError, ValueError, TypeError): return None

def next_action(plan):
    if not plan: return ('Aucun objectif','Choisis un équipement et définis son jet cible.')
    pending=[]; unknown=[]
    for name,pair in plan['stats'].items():
        cur=pair.get('current'); target=pair['target']
        if cur is None: unknown.append(name); continue
        if cur<target: pending.append((target-cur,name,cur,target))
    if pending:
        # Only suggest available rune families. No fabricated likelihood, no automated gameplay.
        _,name,cur,target=max(pending,key=lambda x:x[0])
        gap=target-cur; runes=STATS[name]
        # Conservative tier suggestion, not a claim of optimality or probability.
        rune=runes[0] if gap<3 else (runes[1] if len(runes)>1 else runes[0])
        return (f'À envisager : {rune}', f'{name} : {cur} → {target} (manque {gap}). Vérifie le jet, le puits et le prix avant de poser la rune ; recommandation indicative, non optimisée.')
    if unknown: return ('Jet à lire', 'Jet actuel manquant pour : '+', '.join(unknown)+'. Il faut le lire correctement avant de proposer une rune.')
    return ('Objectif atteint sur les valeurs saisies','Vérifie le jet réel dans DOFUS avant de terminer.')

