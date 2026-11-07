"""Compare DoFocus *user-provided* simulation results to local real trials.

No network, no scraping, no automatic retrieval from DoFocus.
Input columns: source, objet, rune, contexte, resultat, nombre
source: dofocus or forgely; resultat: SC, SN or EC; nombre: integer count.
Equal (objet, rune, contexte) keys are required for comparisons.
"""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

VALID_SOURCES = {'dofocus', 'forgely'}
VALID_OUTCOMES = {'SC','SN','EC'}

def wilson(k, n, z=1.96):
    if n == 0:
        return (0., 1.)
    ph = k/n
    denominator = 1 + z*z/n
    center = (ph + z*z/(2*n))/denominator
    margin = z*math.sqrt((ph*(1-ph)+z*z/(4*n))/n)/denominator
    return max(0, center-margin), min(1, center+margin)

def load(path):
    groups = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'source','objet','rune','contexte','resultat','nombre'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError('Colonnes obligatoires : '+', '.join(sorted(required)))
        for i,row in enumerate(reader,2):
            source=row['source'].strip().lower()
            outcome=row['resultat'].strip().upper()
            try: count=int(row['nombre'])
            except (TypeError,ValueError): raise ValueError(f'Ligne {i}: nombre invalide') from None
            if source not in VALID_SOURCES or outcome not in VALID_OUTCOMES or count<0:
                raise ValueError(f'Ligne {i}: source, résultat ou nombre invalide')
            key=(row['objet'].strip().lower(),row['rune'].strip().lower(),row['contexte'].strip().lower())
            if not all(key): raise ValueError(f'Ligne {i}: objet/rune/contexte obligatoire')
            groups[key][source][outcome]+=count
    return groups

def report(groups):
    lines=['COMPARAISON LOCALE — chiffres issus uniquement de votre CSV','Les résultats d’un simulateur ne sont pas des essais indépendants réels.']
    for key,sources in sorted(groups.items()):
        lines += ['',f'Objet : {key[0]} | Rune : {key[1]} | Contexte : {key[2]}']
        for source in ('dofocus','forgely'):
            counts=sources.get(source,{})
            n=sum(counts.values())
            if not n:
                lines.append(f'  {source}: aucune observation fournie')
                continue
            summary=[]
            for out in ('SC','SN','EC'):
                k=counts.get(out,0)
                rate=100*k/n
                if source=='forgely':
                    lo,hi=wilson(k,n)
                    summary.append(f'{out}: {rate:.1f}% (IC95% {lo*100:.1f}–{hi*100:.1f}%)')
                else:
                    summary.append(f'{out}: {rate:.1f}%')
            lines.append(f'  {source}: n={n} | '+ ' | '.join(summary))
        if 'dofocus' in sources and 'forgely' in sources:
            lines.append('  Comparaison descriptive uniquement : vérifier une configuration strictement identique.')
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Comparaison locale DoFocus / Forgely, sans accès réseau')
    p.add_argument('csv', type=Path)
    a=p.parse_args()
    print(report(load(a.csv)))
