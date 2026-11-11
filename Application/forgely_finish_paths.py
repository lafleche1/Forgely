"""Bounded nominal finishing paths, not full-target success probabilities.

Failures are priced as repeated attempts and uncovered mass. Collateral losses
are unknown; these paths must be recalculated after every observed outcome.
"""
from functools import lru_cache
from forgely_dofocus import RUNE_CHOICES, reference
from forgely_rules import constraints
from forgely_predictive import estimate

STATS = {'Force', 'Intelligence', 'Agilité', 'Chance', 'Sagesse'}


def compare_finish_paths(rows, jets, targets, natural, pool, *, level=None,
                         profile_complete=True):
    comparisons = {}
    if not profile_complete or not natural:
        return comparisons
    for stat in STATS & targets.keys():
        start, goal = jets[stat], targets[stat]
        if start not in (31, 34, 37) or not 0 < goal-start <= 9 or goal > natural.get(stat, 0):
            continue
        roots = {r[1]: r for r in rows if r[2] == stat}
        if len(roots) < 2:
            continue

        def choices(value, reserve):
            for rune in RUNE_CHOICES[stat]:
                ref = reference(rune)
                end = value + ref.gain
                if end > natural[stat]:
                    continue
                state = {**jets, stat: value}
                if constraints({**state, stat: end}, natural)['valid'] is not True:
                    continue
                prediction = (roots[rune][5]['prediction'] if value == start and rune in roots else
                              estimate(state, natural, rune, level=level))
                if not prediction:
                    continue
                success = (prediction['SC'] + prediction['SN']) / 100
                if success <= 0:
                    continue
                # SC preserves reserve; use a conservative nominal debit for
                # subsequent steps. This is exposure, never predicted damage.
                exposure = max(0, ref.weight-reserve)
                cost = (1 + (1-prediction['SC']/100)*exposure) / success
                yield rune, end, max(0, reserve-ref.weight), cost

        @lru_cache(None)
        def best(value, reserve):
            if value >= goal:
                return 0., ()
            paths = []
            for rune, end, remaining, cost in choices(value, reserve):
                tail, path = best(end, remaining)
                paths.append((cost+tail, (rune,)+path))
            return min(paths, default=(float('inf'), ()))

        for rune, end, remaining, cost in choices(start, pool):
            if rune not in roots:
                continue
            tail, path = best(end, remaining)
            if tail == float('inf'):
                continue
            comparisons[rune] = dict(path=[rune, *path], cost=cost+tail,
                source='provisional_nominal_paths', collateral_losses='unknown')
    return comparisons
