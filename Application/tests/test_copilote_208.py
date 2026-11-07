from types import SimpleNamespace
from forgely_copilote import goal_reached, player_signal, budget_summary

def test_goal():
    assert goal_reached({'PA':1,'Vitalité':300},{'PA':1,'Vitalité':300})
    assert not goal_reached({'PA':1},{'PA':1,'Vitalité':300})
    assert not goal_reached({}, {})

def test_stop_and_safety():
    p=SimpleNamespace(rune='Ra Vi',summary='Remonter la vitalité')
    assert player_signal(p,{'Vitalité':300},{'Vitalité':300},10,True,False).stop
    assert not player_signal(p,{'Vitalité':300},{'Vitalité':300},None,True,False).stop
    assert player_signal(p,{'Vitalité':200},{'Vitalité':300},10,True,False).title=='Ra Vi ×1'
    assert player_signal(p,{'Vitalité':200},{'Vitalité':300},10,False,False).title=='Lecture en attente'

def test_budget():
    x=budget_summary({'Ra Vi':4},{'Ra Vi':1200},4000)
    assert x['spent']==4800 and x['over_budget']
