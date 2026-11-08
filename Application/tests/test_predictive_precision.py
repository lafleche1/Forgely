from unittest.mock import patch
import pytest
from forgely_plan import save_plan, load_plan
from forgely_predictive import estimate
from forgely_decision import advise
from forgely_expert import build_dashboard, render_dashboard


def test_level_saved_and_old_plans_remain_compatible(tmp_path):
    path=tmp_path/'objectifs.json'
    p=save_plan('Objet',{'Force':(0,10)},path,level=169)
    assert p['level']==169 and load_plan(path)['level']==169
    p=save_plan('Objet',{'Force':(0,10)},path)
    assert p.get('level') is None
    for invalid in (0,201,True,169.5,'169'):
        with pytest.raises(ValueError):save_plan('Objet',{'Force':(0,10)},path,level=invalid)


def test_display_and_sc_branch_keep_level():
    jets={'Force':0};bounds={'Force':100};targets={'Force':10}
    p=advise(jets,targets,natural_max=bounds,pool=30,level=169)
    with patch('forgely_decision.advise', wraps=advise) as next_advice:
        board=build_dashboard(p,jets,targets,30,natural_max=bounds,level=169)
    assert next_advice.call_args.kwargs['level']==169
    assert '[DIFFICULTÉ]' in render_dashboard(board)
    assert 'niveau' in render_dashboard(board).lower()


def test_exact_q_power_and_correct_tier_units():
    # Three equally weighted LINE ratios: .85,1,1 -> global Q=.95.
    p=estimate({'Force':85,'Chance':100,'Agilité':100},
               {'Force':100,'Chance':100,'Agilité':100},'Ra Fo',level=200)
    assert p['quality']==pytest.approx(.95)
    assert p['terms']['quality']==pytest.approx(32.4216052597582)
    assert p['SC']==pytest.approx(8.7891973701209)
    p=estimate({'Vitalité':75},{'Vitalité':200},'Vi',level=169)
    assert p['terms']['tier']==12 # 75 / gain5 =15; never 75 / weight1
    assert p['terms']['level']==pytest.approx(-20*(1.1-.375))
