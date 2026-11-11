from forgely_decision import advise
from forgely_copilote import player_signal
from forgely_predictive import report_text
from forgely_vision_guidance import reference_for


def test_stable_tetriste_gets_nominal_advice_without_fabricating_signed_odds():
    jet={'Portée':1,'Force':-15,'Intelligence':-15,'Chance':-15,'Agilité':-15}
    targets={stat:0 if value<0 else value for stat,value in jet.items()}
    bounds=reference_for('Amulette Tétriste')
    proposal=advise(jet,targets,pool=0.0,item='Amulette Tétriste',
        natural_max={stat:max(pair) for stat,pair in bounds.items()},profile_complete=True)
    assert proposal.rune is not None
    assert proposal.kind!='bloqué'
    assert proposal.estimates['prediction'] is None
    assert 'malus' in proposal.explanation
    signal=player_signal(proposal,jet,targets,0.0,True,False)
    assert proposal.rune in signal.title
    compact=report_text(proposal,jet,targets,None,0.0,compact=True)
    assert proposal.rune in compact
    assert 'SC/SN/EC non disponibles' in compact
    assert 'Lecture à confirmer' not in compact


def test_a_negative_current_value_does_not_hide_an_already_reached_goal():
    jet={'Force':-15}
    proposal=advise(jet,jet,natural_max=jet,pool=0)
    signal=player_signal(proposal,jet,jet,0,True,False)
    assert proposal.kind=='atteint'
    assert signal.title.startswith('STOP')
