"""Virtual sessions using the advisor model, or explicitly manual legacy scenarios.

Dynamic: python laboratoire_fm.py --contexte contexte.json --sessions 100
The JSON supplies jets, targets, natural_max, pool, prices, optional level/budget.
"""
import argparse
import json
from pathlib import Path
from dataclasses import asdict
from forgely_simulateur import simulate_target
from forgely_simulation_job import simulate_context


def main(argv=None):
    p=argparse.ArgumentParser(description='Laboratoire FM : même modèle dynamique que le copilote')
    p.add_argument('--contexte',type=Path,help='Contexte complet JSON pour le modèle dynamique')
    p.add_argument('--pertes',choices=('stop','uniform'),default='stop',help='uniform : approximation explicite des pertes')
    p.add_argument('--base-reelle',type=Path,help='Base locale facultative : pertes comparables, lecture seule')
    p.add_argument('--manuel',action='store_true',help='Ancien scénario à probabilités fixes')
    p.add_argument('--rune',default='Vi')
    p.add_argument('--actuel',type=float,default=0)
    p.add_argument('--cible',type=float,default=10)
    p.add_argument('--puits',type=float,default=50)
    p.add_argument('--prix',type=float,default=100)
    p.add_argument('--sc',type=float,default=20)
    p.add_argument('--sn',type=float,default=30)
    p.add_argument('--ec',type=float,default=50)
    p.add_argument('--sessions',type=int,default=100)
    p.add_argument('--limite',type=int,default=100)
    p.add_argument('--seed',type=int,default=19)
    a=p.parse_args(argv)
    try:
        if a.contexte and a.manuel:raise ValueError('Choisir --contexte ou --manuel')
        if a.contexte:
            context=json.loads(a.contexte.read_text(encoding='utf-8-sig'))
            result=simulate_context(context,db_file=a.base_reelle,loss_mode=a.pertes,
                trials=a.sessions,max_attempts=a.limite,seed=a.seed)
        elif a.manuel:
            result={'source':'simulation_manuelle_taux_fixes','real_observations_written':0,
                    'resultat':asdict(simulate_target(a.rune,a.actuel,a.cible,a.puits,a.prix,a.sc/100,a.sn/100,a.ec/100,
                        trials=a.sessions,max_attempts=a.limite,seed=a.seed))}
        else:raise ValueError('Fournis --contexte contexte.json, ou --manuel pour un scénario à taux fixes')
    except (ValueError,TypeError,KeyError,OSError) as exc:
        p.error(str(exc))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
