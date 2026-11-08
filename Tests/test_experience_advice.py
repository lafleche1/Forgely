from forgely_decision import candidates,advise
from forgely_online_experience import OnlineExperience


def test_local_experience_changes_candidate_score_immediately():
    model=OnlineExperience()
    jets={'Force':20,'Vitalité':290};targets={'Force':40};bounds={'Force':(1,40),'Vitalité':(1,300)}
    model.observe(1,'Anneau','Fo','SC',{'jet':jets,'pool':5},
        {'jet':{'Force':21,'Vitalité':290},'pool':5})
    baseline=candidates(jets,targets,{'Force':40,'Vitalité':300},5)
    learned=candidates(jets,targets,{'Force':40,'Vitalité':300},5,
        experience_for=lambda rune:model.evaluate('Anneau',rune,jets,5,targets,bounds))
    old=next(row[0] for row in baseline if row[1]=='Fo')
    new=next(row[0] for row in learned if row[1]=='Fo')
    assert old<new<old*1.02


def test_advice_explains_experience_without_inventing_probabilities():
    record={'n':1,'exact':0,'effective_n':.9,'factor':1.005,'kind':'experience_locale_indicative'}
    proposal=advise({'Force':20},{'Force':40},{'Force':40},5,
        experience_for=lambda rune:record)
    assert proposal.estimates['experience']['n']==1
    assert 'expérience locale' in proposal.explanation
    assert proposal.estimates['objective']['goal_probability'] is None


def test_experience_requires_readings_and_ignores_old_budget():
    record={'n':999,'factor':1.1,'kind':'experience_locale_indicative'}
    assert advise({'Force':20},{'Force':40},{'Force':40},None,
        experience_for=lambda rune:record).kind=='bloqué'
    assert advise({'Force':20},{'Force':40},{'Force':40},5,remaining_budget=0,
        experience_for=lambda rune:record).rune is not None


def test_app_uses_complete_bundled_profile_and_cannot_replace_it_with_partial_imports():
    from types import SimpleNamespace
    from unittest.mock import patch
    from forgely import Forgely
    from forgely_labo_live import LiveLaboratory
    app=SimpleNamespace(observation_only=False,
        plan={'item':'Anneau','stats':{'Force':{'target':40}}},
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Anneau'),
        live_jet={'Force':20,'Vitalité':290},live_pool=5,live_after_fusion=False,
        budget_start_cursor=0,live_laboratory=LiveLaboratory('missing-training.db'))
    cfg={'strategy':'Chances maximales','budget_kamas':0,'prices':{}}
    with patch('forgely.read_settings',return_value=cfg), \
         patch('forgely.stats',return_value=(0,{})), \
         patch('forgely.natural_bounds',return_value={'Force':(1,40)}), \
         patch('forgely.complete_learning_profile',return_value={'Force':40,'Vitalité':300}), \
         patch('forgely_decision.natural_profile',return_value=None):
        assert Forgely.strategy_current(app).rune is not None
        app.live_jet={'Force':20}
        assert Forgely.strategy_current(app).kind=='bloqué'
