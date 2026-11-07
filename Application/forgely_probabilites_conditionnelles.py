"""Estimateur empirique conditionnel pour observations FM vérifiées.

Aucune formule secrète supposée. Les classes de contexte ne sont jamais
mélangées; les taux sont descriptifs et accompagnés d'intervalles de Wilson.
"""
from __future__ import annotations
import csv
from collections import Counter, defaultdict
from pathlib import Path
from forgely_validation import VERIFIED_SOURCES, OUTCOMES, wilson

FIELDS = ('date_utc','equipement','rune','resultat','source','jet_avant','puits_avant','type_fm','poids_rune')
TYPES = frozenset(('fm_classique','over','exo'))

def _number(value):
    try:
        n=float(value)
        if not 0 <= n < 1e7: return None
        return n
    except (ValueError,TypeError): return None

def _pool_band(n):
    if n == 0: return '0'
    if n < 10: return '0-10'
    if n < 30: return '10-30'
    if n < 100: return '30-100'
    return '100+'

def _weight_band(n):
    if n <= 10: return '<=10'
    if n <= 30: return '10-30'
    if n <= 60: return '30-60'
    return '>60'

def audit_conditional(path, *, minimum=50):
    if not 1 <= minimum <= 100000: raise ValueError('minimum invalide')
    groups=defaultdict(Counter); rejected=Counter(); seen=set()
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError('Colonnes manquantes : '+', '.join(sorted(set(FIELDS)-set(reader.fieldnames or []))))
        for row in reader:
            source=(row['source'] or '').strip()
            if source not in VERIFIED_SOURCES:
                rejected['non_verifie']+=1;continue
            item=(row['equipement'] or '').strip(); rune=(row['rune'] or '').strip()
            outcome=(row['resultat'] or '').strip().upper(); kind=(row['type_fm'] or '').strip()
            pool=_number(row['puits_avant']); weight=_number(row['poids_rune'])
            # Jet avant must be present and independently checked; do not infer
            # natural caps, relative stat level or outcomes from its free text.
            jet=(row['jet_avant'] or '').strip()
            if not item or not rune or not jet or pool is None or weight is None or kind not in TYPES or outcome not in OUTCOMES:
                rejected['contexte_incomplet']+=1;continue
            timestamp=(row['date_utc'] or '').strip()
            if not timestamp:
                rejected['date_absente']+=1;continue
            signature=(timestamp,item,rune,outcome,source,jet,pool,weight,kind)
            if signature in seen:
                rejected['doublon']+=1;continue
            seen.add(signature)
            key=(item,rune,kind,_pool_band(pool),_weight_band(weight))
            groups[key][outcome]+=1
    result=[]
    for key,counts in sorted(groups.items()):
        n=sum(counts.values())
        result.append({'equipement':key[0],'rune':key[1],'type_fm':key[2],
                       'classe_puits':key[3],'classe_poids':key[4],
                       'n':n,'comptages':{o:counts[o] for o in OUTCOMES},
                       'frequences':{o:round(counts[o]/n,5) for o in OUTCOMES} if n>=minimum else None,
                       'ic95_wilson':{o:wilson(counts[o],n) for o in OUTCOMES} if n>=minimum else None,
                       'utilisable':n>=minimum})
    return {'type':'frequences_conditionnelles_observees','probabilites_officielles':False,
            'simulations_incluses':False,'minimum':minimum,'rejets':dict(rejected),
            'note':'Classes larges; jet exact et autres variables non contrôlés. Biais de sélection possibles. Ne pas généraliser.',
            'groupes':result}

def estimate(report, *, equipement, rune, type_fm, puits, poids):
    """Return an empirical group only when the complete matching context is present."""
    if puits is None or poids is None: return None
    p=_number(puits); w=_number(poids)
    if p is None or w is None: return None
    for group in report.get('groupes',()):
        if (group['equipement'],group['rune'],group['type_fm'],group['classe_puits'],group['classe_poids']) == (equipement,rune,type_fm,_pool_band(p),_weight_band(w)) and group['utilisable']:
            return group
    return None
