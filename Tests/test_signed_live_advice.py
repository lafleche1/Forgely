import pytest
from forgely_decision import advise,candidates
from forgely_dofocus import RUNE_CHOICES,reference


def forbidden(*args,**kwargs):
    raise AssertionError('Signed live advice must not use a simulator')


@pytest.mark.parametrize('current,goal,cap', [(-15,0,-15),(-15,-10,-15),(-1,0,-15),
    (-5,5,40),(0,3,-15),(3,6,-15)])
def test_signed_force_goals_get_a_nominal_recommendation_without_simulation(current,goal,cap):
    proposal=advise({'Force':current},{'Force':goal},{'Force':cap},0,
        predictive_policy=True,simulation_for=forbidden)
    assert proposal.rune in RUNE_CHOICES['Force']
    assert proposal.estimates['prediction'] is None
    assert proposal.estimates['local_simulation'] is None
    assert 'nominal' in proposal.explanation.lower()
    assert all(x['probabilities'] is None for x in proposal.estimates['matrix']['choices'])
    assert all(x['pool_SN_EC_without_losses']=='inconnu' for x in proposal.estimates['matrix']['choices'])


def test_tetriste_recommends_a_rune_for_a_confirmed_deficit():
    from forgely_vision_guidance import reference_for
    jet={'Portée':1,'Force':-15,'Intelligence':-15,'Chance':-15,'Agilité':-15}
    target={s:0 if v<0 else v for s,v in jet.items()}
    p=advise(jet,target,{s:max(v) for s,v in reference_for('Amulette Tétriste').items()},
             0,item='Amulette Tétriste',predictive_policy=True,simulation_for=forbidden)
    assert p.rune
    assert any(p.rune in RUNE_CHOICES[s] for s in ('Force','Intelligence','Chance','Agilité'))


def test_a_malus_elsewhere_does_not_block_a_positive_line_repair():
    p=advise({'Force':30,'Chance':-10},{'Force':40,'Chance':-10},
             {'Force':40,'Chance':-10},3,predictive_policy=True)
    assert p.rune in RUNE_CHOICES['Force']


def test_negative_target_does_not_leak_probabilities_through_tier_comparison():
    p=advise({'Force':30,'Chance':0},{'Force':40,'Chance':-1},
             {'Force':40,'Chance':10},0,predictive_policy=True)
    assert p.estimates['signed_profile']
    for rows in p.estimates['tier_comparison'].values():
        for row in rows:
            assert row['probabilities'] is None
            assert row['expected_capped_progress'] is None


def test_signed_profiles_still_require_complete_readings_and_pool():
    for jet,goal,pool in [({'Force':-15},{'Force':0,'Chance':0},0),
                           ({'Force':-15},{'Force':0},None)]:
        assert advise(jet,goal,{'Force':-15},pool).rune is None
    assert advise({'Force':-15},{'Force':-15},{'Force':-15},0).kind=='atteint'


def test_signed_pool_transfer_is_not_invented_from_positive_line_weights():
    from forgely_pool_ledger import PoolLedger
    from forgely_expert import audit_transition
    before={'jet':{'Force':-15},'pool':2.0}
    after={'jet':{'Force':-14},'pool':1.5}
    ledger=PoolLedger();ledger.observe(2,'item')
    assert float(ledger.apply(before['jet'],after['jet'],'Fo','SN',1,'item',True)) == 1.5
    assert ledger.origin=='calculated'
    assert ledger.observe(1.5,'item') is not None
    audit=audit_transition('Fo','SN',before,after,complete=True)
    assert audit['status']=='cohérent'
    assert audit['calculated_pool'] == 1.5


def test_every_catalogue_malus_profile_with_runes_can_offer_signed_advice():
    from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
    from forgely_dofocus import canonical_stat
    checked=0
    for item in EquipmentCatalog().items:
        bounds={canonical_stat(s):pair for s,pair in equipment_bounds(item).items()}
        negative=[s for s,pair in bounds.items() if max(pair)<0 and s in RUNE_CHOICES]
        if not negative:continue
        jet={s:max(pair) for s,pair in bounds.items()}
        target=dict(jet)
        for stat in negative:target[stat]=0
        p=advise(jet,target,{s:max(pair) for s,pair in bounds.items()},0,predictive_policy=True)
        assert p.rune, (item.name,p.summary,p.explanation)
        checked+=1
    assert checked>10


def test_live_copilot_recommends_on_confirmed_tetriste_without_simulation(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from forgely import Forgely
    from forgely_workshop_readings import WorkshopReadings
    from forgely_vision_guidance import reference_for
    from forgely_simulation_live import SimulationWorker
    monkeypatch.setattr(SimulationWorker,'context',forbidden)
    jet={'Portée':1,'Force':-15,'Intelligence':-15,'Chance':-15,'Agilité':-15}
    goal={s:0 if v<0 else v for s,v in jet.items()}
    name='Amulette Tétriste'
    readings=WorkshopReadings();readings.configure(('confirmed',name),reference_for(name))
    for frame in range(3):readings.observe(jet,0,sequence=frame)
    item=Mock();item.get.return_value=name
    app=SimpleNamespace(observation_only=False,running=True,workshop_active=True,
        active_equipment_verified=True,workshop_readings=readings,_copilot_masked=False,
        measured_goals=None,item=item,live_jet=jet,live_pool=0,live_after_fusion=False,
        plan={'item':name,'level':55,'stats':{s:{'target':v} for s,v in goal.items()}},
        live_laboratory=SimpleNamespace(estimate=lambda *args:None))
    monkeypatch.setattr('forgely.read_settings',lambda:{})
    monkeypatch.setattr('forgely.learning_sources',lambda *args:({},None))
    proposal=Forgely._strategy_current(app)
    assert proposal.rune
    assert proposal.estimates['signed_profile'] is True
    assert proposal.estimates['local_simulation'] is None
