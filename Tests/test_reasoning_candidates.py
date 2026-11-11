from forgely_reasoning import strategic_options, explain_choice
from forgely_rl import ForgemagingEnv
from forgely_training import TrainingConfig, _prepare, _heuristic, state_key, run_training


def lines():
    return [dict(stat='Intelligence',value=40,min=30,max=40,weight=1),
            dict(stat='Force',value=30,min=30,max=40,weight=1)]


def test_preparatory_over_is_an_option_not_already_credited_pool():
    choices=strategic_options({'Intelligence':40,'Force':30},{'Intelligence':40,'Force':40},
                             {'Intelligence':40,'Force':40},17)
    ine=next(x for x in choices if x['rune']=='Ine' and x['experimental'])
    assert ine['purpose']=='temporary_surplus' and ine['pool_gain_guaranteed']==0
    assert 'SC' in ine['explanation']
    assert strategic_options({'Intelligence':40},{'Intelligence':40},{'Intelligence':40},0)==[]


def test_no_fabricated_exo_or_unbounded_over_or_malus_strategy():
    assert not any(x['rune']=='Ine' for x in strategic_options({'Intelligence':43,'Force':30},
        {'Intelligence':40,'Force':40},{'Intelligence':40,'Force':40},0) if x['experimental'])
    assert not strategic_options({'Sagesse':-8},{'Sagesse':0},{'Sagesse':-8},0)


def test_trainer_explores_optional_preparation_and_encodes_exact_surplus():
    env=ForgemagingEnv(lines(),17,{'Intelligence':40,'Force':40},allow_preparatory=True)
    assert 'Ine' in env.get_valid_actions()
    assert _heuristic(env,env.get_valid_actions())!='Ine'
    before=state_key(env.get_state());env.lines[0]['value']=41
    assert before!=state_key(env.get_state())
    base=ForgemagingEnv(lines(),17,{'Intelligence':40,'Force':40})
    assert 'Ine' not in base.get_valid_actions()
    assert env.pool==17


def test_choice_explains_weight_target_and_pool_without_free_success_claim():
    text=explain_choice('Pa Ine',{'Intelligence':38},{'Intelligence':40},{'Intelligence':40},2)
    assert '3' in text and '2' in text and 'cible' in text
    assert 'garanti' in text


def test_training_modes_do_not_resume_each_others_policies_and_are_auditable(tmp_path):
    cfg=TrainingConfig(item_id=14092,targets={'Intelligence':40,'Force':40},episodes=2,
                       max_steps=5,evaluation_episodes=2,allow_preparatory=True)
    prepared=_prepare(cfg)
    classic=_prepare(TrainingConfig(item_id=14092,targets=cfg.targets,episodes=2,max_steps=5,evaluation_episodes=2))
    assert prepared[3]!=classic[3]
    result=run_training(cfg,tmp_path)
    assert result['configuration']['allow_preparatory'] is True
    assert result['real_observations']==0
    assert not result['eligible_for_advice']
