"""Laboratoire de simulation indépendant de l’interface Forgely.

Exemple : python laboratoire_fm.py --rune Vi --actuel 0 --cible 10 --puits 50 --prix 100 --sc 20 --sn 30 --ec 50
Les probabilités sont des hypothèses, non des taux observés dans DOFUS.
"""
import argparse
import json
from dataclasses import asdict
from forgely_simulateur import simulate_target


def main():
    p = argparse.ArgumentParser(description="Laboratoire FM expérimental, indépendant de Forgely")
    p.add_argument('--rune', default='Vi')
    p.add_argument('--actuel', type=float, default=0)
    p.add_argument('--cible', type=float, default=10)
    p.add_argument('--puits', type=float, default=50)
    p.add_argument('--prix', type=float, default=100)
    p.add_argument('--sc', type=float, default=20, help='Pourcentage hypothétique')
    p.add_argument('--sn', type=float, default=30, help='Pourcentage hypothétique')
    p.add_argument('--ec', type=float, default=50, help='Pourcentage hypothétique')
    p.add_argument('--sessions', type=int, default=2000)
    p.add_argument('--limite', type=int, default=100)
    p.add_argument('--seed', type=int, default=19)
    a=p.parse_args()
    result=simulate_target(a.rune,a.actuel,a.cible,a.puits,a.prix,a.sc/100,a.sn/100,a.ec/100,
        trials=a.sessions,max_attempts=a.limite,seed=a.seed)
    print(json.dumps({'modele':'hypothetique_simplifie','taux_reels_valides':False,
                      'resultat':asdict(result)},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
