"""Read-only executable audit of current behavior, not server validation.

Run from any directory. Known divergences are observations, not desired contracts.
Only audit output files are written; application sources are never changed.
"""
import hashlib
import json
from pathlib import Path
from random import Random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'Application'))
from forgely_decision import advise, candidates, pool_transition
from forgely_dofocus import reference
from forgely_dofocus_engine import attempt, odds
from forgely_predictive import estimate
from forgely_reasoning import strategic_options
from forgely_rules import constraints
from forgely_virtual import apply_outcome
from forgely_pool_ledger import PoolLedger
from forgely_rl import ForgemagingEnv
from forgely_training import _heuristic


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inventory():
    return {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p)
            for p in sorted((ROOT / 'Application').rglob('*.py'))}


def main():
    before = source_inventory()
    records = []

    def checked(name, condition, details):
        assert condition, name
        records.append(dict(name=name, verified=True, details=details))

    expected = {'Ra Ine': (10, 10), 'Do': (1, 20), 'Do Feu': (1, 5),
                'Cri': (1, 10), 'Ga Pa': (1, 100), 'Ga Pme': (1, 90),
                'Po': (1, 51), 'Ra Vi': (50, 10)}
    checked('rune_weights', all((reference(r).gain, reference(r).weight) == value
                               for r, value in expected.items()), expected)
    lines = [dict(stat='Intelligence', value=20, min=0, max=40, weight=1),
             dict(stat='Force', value=40, min=0, max=40, weight=1)]
    rune = dict(stat='Intelligence', gain=10, weight=10)
    for outcome in ('SC', 'SN', 'EC'):
        result = attempt(lines, rune, 2, rng=Random(19),
                         probabilities={k: 100 if k == outcome.lower() else 0
                                        for k in ('sc', 'sn', 'ec')})
        values = {line['stat']: line['value'] for line in result['lines']}
        expected_values = dict(Intelligence=30 if outcome != 'EC' else 20,
                               Force=40 if outcome == 'SC' else 32)
        checked('insufficient_pool_' + outcome,
                result['pool'] == (2 if outcome == 'SC' else 0)
                and values == expected_values, dict(pool=result['pool'], values=values))
    checked('unknown_losses_are_not_free',
            apply_outcome({'Intelligence':20,'Force':40},2,'Ra Ine','SN') is None,
            'Dynamic simulator censors insufficient-pool transitions without losses.')
    ledger = PoolLedger()
    ledger.observe(0, 'audit')
    value = ledger.apply({'Force':10,'PA':1}, {'Force':11,'PA':0},
                         'Fo','SN',1,'audit',True)
    checked('released_PA_minus_rune', value == 99, str(value))
    checked('SC_keeps_pool', pool_transition(2,10,0,'SC') == 2, 'SC: pool remains 2.')
    checked('line_over_cap',
            constraints({'Force':101},{'Force':100})['valid'] is True
            and constraints({'Force':102},{'Force':100})['valid'] is False,
            '101 is the resulting line density guard, not +101 over the maximum.')
    checked('natural_repass_is_not_exo',
            advise({'Force':40,'PA':0},{'Force':41,'PA':1},
                   natural_max={'Force':40,'PA':1},pool=0).rune == 'Ga Pa',
            'Missing natural PA restored before final over; no universal last-PA rule.')
    checked('stop_at_goal',
            advise({'Force':40},{'Force':40},natural_max={'Force':40},pool=0).rune is None,
            'No automatic exo or max+1 once goal is reached.')
    preparations = strategic_options({'Intelligence':40,'Force':30},
                                    {'Intelligence':40,'Force':40},
                                    {'Intelligence':40,'Force':40},17)
    checked('no_credited_future_pool', all(p['pool_gain_guaranteed'] == 0 for p in preparations),
            'Temporary surplus is experimental, never already acquired pool.')
    blockers = []
    for jets, goals, bounds, pool in [({'Force':20},{'Force':40},{'Force':40},51),
                                     ({'Dommages':0},{'Dommages':1},{'Dommages':1},2)]:
        normal = advise(jets,goals,natural_max=bounds,pool=pool)
        matrix = advise(jets,goals,natural_max=bounds,pool=pool,predictive_policy=True)
        checked('phase_filter_block_' + str(pool), normal.rune is not None and matrix.rune is None,
                dict(pool=pool, normal=normal.rune, matrix=matrix.summary))
        blockers.append(matrix.summary)
    env = ForgemagingEnv([dict(stat='Force',value=20,min=0,max=40,weight=1)],51,{'Force':40})
    checked('trainer_still_acts_when_matrix_blocks',
            _heuristic(env,env.get_valid_actions()) != 'stop',
            dict(action=_heuristic(env,env.get_valid_actions()), pool=51))
    exo_lines = [dict(stat='Force',value=40,min=0,max=40,weight=1)]
    local = odds(exo_lines,dict(stat='PA',gain=1,weight=100))
    video = estimate({'Force':40,'PA':0},{'Force':40},'Ga Pa')
    checked('exo_probability_disagreement', local['sc'] == 1.5 and video['SC'] == 1,
            dict(dofocus_SC=local['sc'], video_SC=video['SC'], official_verified=False))
    # The simulator caps its pool, whereas the observation ledger does not.
    r = attempt([dict(stat='Force',value=10,min=0,max=40,weight=1)],
                dict(stat='Force',gain=1,weight=1),150,rng=Random(19),
                probabilities={'sc':0,'sn':100,'ec':0})
    checked('pool_cap_disagreement', r['pool'] == 100 and pool_transition(150,1,0,'SN') == 149,
            dict(dofocus=r['pool'], accounting=149))
    remote = json.loads((HERE / 'github-sources.json').read_text(encoding='utf8'))
    comparison = []
    for row in remote['files']:
        raw = row['content'].encode('utf8')
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        assert blob == row['sha'], row['path']
        path = ROOT / row['path']
        comparison.append(dict(path=row['path'], github_blob_sha=row['sha'],
                               local_sha256=digest(path),
                               same_text=path.read_text(encoding='utf8') == row['content']))
    after = source_inventory()
    checked('application_sources_preserved', before == after,
            dict(python_files=len(before), changed=[]))
    result = dict(scope='Local model and source audit; no game/server experiments',
                  checks=records, github_ref=remote['ref'], comparison=comparison,
                  application_sha256=after)
    (HERE / 'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(f'{len(records)} audit checks passed; {len(before)} Python source hashes unchanged.')
    print(json.dumps(comparison,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
