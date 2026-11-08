import json
from pathlib import Path
import pytest
from forgely_dofocus_engine import odds,attempt

FIXTURE=json.loads((Path(__file__).parent/'fixtures/dofocus_engine_cases.json').read_text(encoding='utf-8'))


class RandomSequence:
    def __init__(self,seed):self.value=seed
    def random(self):
        self.value=(1664525*self.value+1013904223)&0xffffffff
        return self.value/4294967296


@pytest.mark.parametrize('case',FIXTURE['cases'])
def test_odds_match_public_engine(case):
    result=odds(case['lines'],case['rune'],level=case['level'])
    for key,value in case['odds'].items():
        assert key in result
        if type(value) in (int,float):assert result[key]==pytest.approx(value,abs=1e-9)
        else:assert result[key]==value


@pytest.mark.parametrize('case',FIXTURE['cases'])
def test_transitions_match_public_engine_without_modifying_input(case):
    saved=json.dumps(case,sort_keys=True)
    for expected in case['attempts']:
        result=attempt(case['lines'],case['rune'],case['pool'],level=case['level'],rng=RandomSequence(expected['seed']))
        assert result['outcome']==expected['outcome']
        assert result['pool']==pytest.approx(expected['pool'])
        assert {l['stat']:l['value'] for l in result['lines']}=={l['stat']:l['value'] for l in expected['values']}
    assert json.dumps(case,sort_keys=True)==saved


@pytest.mark.parametrize('bad',[True,float('nan'),float('inf'),-1])
def test_invalid_pools_fail_closed(bad):
    with pytest.raises(ValueError):attempt(FIXTURE['cases'][0]['lines'],FIXTURE['cases'][0]['rune'],bad)
