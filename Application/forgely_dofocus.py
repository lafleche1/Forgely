"""Versioned Dofocus reference; simulator displays are never real game trials.

No network calls, no game actions and no writes to the observation database.
Only full, equal starting states may reuse a recorded percentage display.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from math import isfinite
import json
import unicodedata
from datetime import date

SOURCE_URL = 'https://dofocus.fr/forgemagie/'
GUIDE_URL = 'https://dofocus.fr/guide/'
REFERENCE_PATH = Path(__file__).with_name('references') / 'dofocus' / 'reference.json'
STORE_PATH = Path(__file__).with_name('assets') / 'dofocus' / 'reference.sqlite3'


def key(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(text)).casefold()
                            if not unicodedata.combining(c)).split())


# Gains/weights: simulator (Vi +5 weighs 1) takes precedence over the
# brisage guide's ambiguous Vi wording. No success percentages in this table.
FAMILIES = {
    'Vitalité': ('Vi',5,.2,(1,3,10)),
    'Force': ('Fo',1,1,(1,3,10)), 'Intelligence': ('Ine',1,1,(1,3,10)),
    'Chance': ('Cha',1,1,(1,3,10)), 'Agilité': ('Age',1,1,(1,3,10)),
    'Sagesse': ('Sa',1,3,(1,3,10)), 'Puissance': ('Pui',1,2,(1,3,10)),
    'Initiative': ('Ini',10,.1,(1,3,10)), 'Prospection': ('Prospe',1,3,(1,3)),
    'Pods': ('Pod',10,.25,(1,3,10)), 'PA': ('Ga Pa',1,100,(1,)),
    'PM': ('Ga Pme',1,90,(1,)), 'Portée': ('Po',1,51,(1,)),
    'Invocations': ('Invo',1,30,(1,)), 'Coups Critiques': ('Cri',1,10,(1,)),
    'Soins': ('So',1,10,(1,3)), 'Tacle': ('Tac',1,4,(1,3)),
    'Fuite': ('Fui',1,4,(1,3)), 'Dommages': ('Do',1,20,(1,)),
    'Dommages Critiques': ('Do Cri',1,5,(1,3)),
    'Dommages Poussée': ('Do Pou',1,5,(1,3)),
    'Dommages Pièges': ('Do Pi',1,5,(1,3)),
    'Puissance Pièges': ('Per Pi',1,2,(1,3,10)),
    'Résistance Critique': ('Ré Cri',1,2,(1,3,10)),
    'Résistance Poussée': ('Ré Pou',1,2,(1,3,10)),
    'Esquive PA': ('Ré Pa',1,7,(1,3)), 'Esquive PM': ('Ré Pme',1,7,(1,3)),
    'Retrait PA': ('Ret Pa',1,7,(1,3)), 'Retrait PM': ('Ret Pme',1,7,(1,3)),
}
for element in ('Neutre','Terre','Feu','Eau','Air'):
    FAMILIES[f'Dommages {element}']=(f'Do {element}',1,5,(1,3))
    FAMILIES[f'Résistance {element}']=(f'Ré {element}',1,2,(1,3,10))
    FAMILIES[f'% Résistance {element}']=(f'Ré Per {element}',1,6,(1,))

ALIASES = {key(s):s for s in FAMILIES}
ALIASES.update({key("Points d'action (PA)"):'PA',key('Points de mouvement (PM)'):'PM',
                key('Coups Critiques (%)'):'Coups Critiques',key('Invocation'):'Invocations',
                key('Résistances Critiques (fixe)'):'Résistance Critique',
                key('Résistance Poussée (fixe)'):'Résistance Poussée',
                key('Résistances Poussée (fixe)'):'Résistance Poussée'})
for element in ('Neutre','Terre','Feu','Eau','Air'):
    ALIASES[key(f'Dommages {element} (fixe)')]=f'Dommages {element}'
    for prefix in ('Résistance','Résistances'):
        ALIASES[key(f'{prefix} {element} (fixe)')]=f'Résistance {element}'
        ALIASES[key(f'{prefix} {element}')]=f'Résistance {element}'
        ALIASES[key(f'{prefix} {element} (%)')]=f'% Résistance {element}'
        ALIASES[key(f'% {prefix} {element}')]=f'% Résistance {element}'


def canonical_stat(stat):
    return ALIASES.get(key(stat), str(stat))


def finite_number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value)


def normalise_jet(jets):
    if not isinstance(jets,dict):return None
    result={}
    for stat,value in jets.items():
        if not finite_number(value):return None
        name=canonical_stat(stat)
        if name in result:return None  # duplicate aliases make completeness ambiguous
        result[name]=value
    return result


@dataclass(frozen=True)
class RuneReference:
    name: str
    gain: float | None
    weight: float | None


RUNE_CHOICES = {}
RUNE_REFERENCES = {}
WEIGHT_PER_POINT = {}
for _stat,(_name,_gain,_unit,_tiers) in FAMILIES.items():
    WEIGHT_PER_POINT[_stat]=_unit
    RUNE_CHOICES[_stat]=[]
    for _prefix,_mult in zip(('', 'Pa ', 'Ra '),_tiers):
        _rune=_prefix+_name
        RUNE_CHOICES[_stat].append(_rune)
        RUNE_REFERENCES[_rune]=RuneReference(_rune,_gain*_mult,_gain*_mult*_unit)


def reference(rune):
    return RUNE_REFERENCES.get(rune,RuneReference(rune,None,None))


def displayed_number(text):
    if not isinstance(text,str):raise ValueError('Pourcentage affiché invalide')
    value=float(text.removeprefix('≈').replace(',','.'))
    if not isfinite(value) or not 0<=value<=100:raise ValueError('Pourcentage hors limites')
    return value


def validate_catalogue(data):
    try:
        return _validate_catalogue(data)
    except (AttributeError,KeyError,TypeError,IndexError) as error:
        raise ValueError('Structure du référentiel invalide') from error


def _validate_catalogue(data):
    if not isinstance(data,dict) or data.get('source')!='Dofocus':
        raise ValueError('Provenance Dofocus requise')
    captured=data.get('captured_on')
    if not isinstance(captured,str) or date.fromisoformat(captured).isoformat()!=captured:
        raise ValueError('Date de consultation invalide')
    if not isinstance(data.get('snapshots'),list):raise ValueError('Liste de contextes attendue')
    if data.get('schema')!=1 or data.get('kind')!='simulation_reference' or type(data.get('real_attempts')) is not int or data['real_attempts']!=0:
        raise ValueError('Référence de simulation attendue')
    if not data.get('snapshots'):raise ValueError('Référence vide')
    seen=set()
    for sample in data['snapshots']:
        if not isinstance(sample,dict) or not isinstance(sample.get('item'),str) or not sample['item'].strip():
            raise ValueError('Objet invalide')
        if not isinstance(sample.get('rows'),list) or not sample['rows']:raise ValueError('Lignes attendues')
        ident=sample['item_id']
        if type(ident) is not int or ident<=0 or sample['url']!=SOURCE_URL+str(ident):
            raise ValueError('URL de provenance invalide')
        if not finite_number(sample['pool']) or sample['pool']<0:raise ValueError('Reliquat invalide')
        jet={}
        for row in sample['rows']:
            if not isinstance(row,dict) or not isinstance(row.get('runes'),dict):raise ValueError('Ligne invalide')
            name=canonical_stat(row['stat'])
            if name not in RUNE_CHOICES:raise ValueError('Caractéristique inconnue')
            if name in jet or not finite_number(row['value']):raise ValueError('Jet ambigu')
            jet[name]=row['value']
            lo,hi=row['min'],row['max']
            if (lo is None)!=(hi is None):raise ValueError('Bornes incomplètes')
            if lo is not None and (not finite_number(lo) or not finite_number(hi) or lo>hi):
                raise ValueError('Bornes invalides')
            for rune,result in row['runes'].items():
                if rune not in RUNE_CHOICES[name]:raise ValueError('Rune attribuée à une autre caractéristique')
                if not isinstance(result,dict) or type(result.get('blocked')) is not bool:raise ValueError('Résultat invalide')
                if result['blocked']:
                    if not finite_number(result['line_max']):raise ValueError('Plafond invalide')
                    continue
                if set(result['display'])!={'SC','SN','EC'}:raise ValueError('Résultats incomplets')
                values=[displayed_number(result['display'][k]) for k in ('SC','SN','EC')]
                # Displayed, independently rounded percentages need not sum to exactly 100.
                if abs(sum(values)-100)>1.5:raise ValueError('Pourcentages incohérents')
                ref=reference(rune)
                if ref.weight is None or not finite_number(result['weight']) or abs(ref.weight-result['weight'])>1e-6:
                    raise ValueError('Poids incohérent : '+rune)
        signature=(key(sample['item']),tuple(sorted(jet.items())),sample['pool'])
        if signature in seen:raise ValueError('Contexte dupliqué')
        seen.add(signature)
    return data


@lru_cache(maxsize=1)
def catalogue():
    try:
        return validate_catalogue(json.loads(REFERENCE_PATH.read_text(encoding='utf-8')))
    except (OSError,ValueError,KeyError,TypeError):
        # Missing/broken reference disables exact displays, never invents rates.
        return {'schema':1,'kind':'simulation_reference','real_attempts':0,'snapshots':[]}


@lru_cache(maxsize=1)
def _cached_store(path,stamp,size):
    from forgely_dofocus_store import ReferenceStore
    return ReferenceStore(path)


def reference_store():
    try:
        info=STORE_PATH.stat()
        stamp,size=info.st_mtime_ns,info.st_size
    except OSError:
        stamp,size=None,None
    return _cached_store(str(STORE_PATH),stamp,size)


def natural_profile(item):
    return reference_store().profile(item)


def lookup_context(item,jets,pool):
    return reference_store().context(item,jets,pool)


def lookup(item,jets,pool,rune):
    return reference_store().rune(item,jets,pool,rune)


def line_limit(item,stat):
    return reference_store().limit(item,stat)


def risk_notes(current, proposed, weight, pool, natural_max=None):
    notes=['Référence : Dofocus — '+SOURCE_URL]
    if current<0:
        notes.append('Ligne en malus : le simulateur affiche un coût réduit de moitié ; le franchissement de zéro nécessite un relevé spécifique.')
    if natural_max is None:
        notes.append('Bornes naturelles inconnues : type de tentative non vérifiable.')
    elif proposed>natural_max:
        notes.append('Le gain proposé dépasse le maximum naturel : vérifier le risque d’over ou d’exo dans le simulateur.')
    if pool<weight:
        notes.append('Reliquat inférieur au poids nominal : les autres lignes peuvent être exposées à une perte.')
    else:
        notes.append('Reliquat au moins égal au poids nominal ; cela ne garantit pas le passage.')
    return notes
