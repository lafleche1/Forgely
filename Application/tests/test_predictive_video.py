import pytest
import forgely_predictive as model
from forgely_decision import advise


def predict(current=0, gain=1, maximum=100, **kw):
    return model.estimate({'Force':current}, {'Force':maximum}, 'Fo' if gain==1 else 'Ra Fo', **kw)


def test_threshold_and_ratio():
    assert predict(0)['SC']==47.5
    assert predict(79,gain=10)['terms']['threshold']==0
    assert predict(80,gain=10)['terms']['threshold']==45
    assert predict(14)['terms']['tier']==0
    assert predict(15)['terms']['tier']==12


def test_over_quality_and_level():
    result=predict(100)
    assert result['terms']['over']==69
    assert predict(0,level=169)['terms']['level']==-22
    assert predict(0,level=170)['terms']['level']==0
    assert 'niveau inconnu' in ' '.join(predict(0)['assumptions'])
    a=model.estimate({'Force':0,'PA':1},{'Force':100},'Fo')
    assert a['quality']==1 and a['terms']['quality']==60
    assert a['difficulty']==65


def test_probability_domains_and_heavy_exo():
    for v in (0,14,80,100,500):
        p=predict(v)
        assert sum(p[k] for k in ('SC','SN','EC'))==pytest.approx(100)
        assert all(0<=p[k]<=100 for k in ('SC','SN','EC'))
    p=model.estimate({'Force':0,'PA':0},{'Force':100},'Ga Pa')
    assert (p['SC'],p['SN'],p['EC'])==(1,0,99)
    assert model.estimate({'Force':0},None,'Fo') is None
    assert model.estimate({'Force':0},{'Force':100,'Vitalité':300},'Fo') is None
    assert model.estimate({'Force':float('nan')},{'Force':100},'Fo') is None


def test_calibration_uses_only_qualified_counts():
    p=predict(0)
    assert model.calibrate(p,{'counts':{'SC':100,'SN':0,'EC':0},'verified':False})['SC']==47.5
    q=model.calibrate(p,{'counts':{'SC':100,'SN':0,'EC':0},'verified':True})
    assert q['SC']==pytest.approx(65)
    assert q['real_weight']==pytest.approx(1/3)
    assert sum(q[k] for k in ('SC','SN','EC'))==pytest.approx(100)
    assert model.calibrate(p,{'counts':{'SC':29},'verified':True})['SC']==47.5


def test_active_advisor_exposes_and_uses_prediction():
    p=advise({'Force':0},{'Force':10},natural_max={'Force':100},pool=30)
    assert p.estimates['prediction']['SC']==47.5
    assert 'estim' in p.explanation.lower()
    assert p.estimates['objective']['alternatives'][0]['prediction'] is not None
    q=advise({'Force':0},{'Force':10},natural_max={'Force':100},pool=30,
             context_for=lambda rune:{'verified':True,'counts':{'SC':100}})
    assert q.estimates['prediction']['real_weight']>0


def test_real_contexts_certify_only_complete_consistent_transitions(tmp_path):
    from forgely_context import save_transition
    from forgely_labo_live import compute_snapshot, LiveLaboratory
    db=tmp_path/'trials.db'
    before={'jet':{'Force':0},'pool':10}
    after={'jet':{'Force':1},'pool':10}
    for _ in range(30):
        save_transition('Test','Fo','SC',before,after,db_file=db,
                        natural_max={'Force':100},complete=True)
    save_transition('Test','Fo','SC',before,after,db_file=db)
    bad={'jet':{'Force':1},'pool':9}
    save_transition('Test','Fo','SC',before,bad,db_file=db,
                    natural_max={'Force':100},complete=True)
    lab=LiveLaboratory(db)
    lab._snapshot=compute_snapshot(db)
    sample=lab.calibration('Test','Fo',{'Force':0},10)
    assert sample['counts']['SC']==30 and sample['verified']
    assert lab.calibration('Test','Fo',{'Force':0},11) is None
    # A loss-free EC must also count; otherwise the dataset selects only visible changes.
    for _ in range(30):
        save_transition('Test','Fo','EC',{'jet':{'Force':0},'pool':0},
                        {'jet':{'Force':0},'pool':0},db_file=db,
                        natural_max={'Force':100},complete=True)
    lab._snapshot=compute_snapshot(db)
    assert lab.calibration('Test','Fo',{'Force':0},0)['counts']['EC']==30


def test_dashboard_reports_estimated_odds_not_final_goal_probability():
    from forgely_expert import build_dashboard, render_dashboard, rules_text
    p=advise({'Force':0},{'Force':10},natural_max={'Force':100},pool=30)
    board=build_dashboard(p,{'Force':0},{'Force':10},30,natural_max={'Force':100})
    assert board['prediction']['SC']==47.5
    assert '[PROBABILITÉS ESTIMÉES]' in render_dashboard(board)
    assert board['goal_probability'] is None
    assert '200' in rules_text()


def test_chance_mode_accepts_natural_surplus_when_small_rune_is_saturated():
    args=dict(jets={'Vitalité':299},targets={'Vitalité':300},natural_max={'Vitalité':350},pool=10)
    chance=advise(**args)
    assert chance.rune=='Ra Vi'
    economy=advise(**args,mode='Budget optimisé',prices={'Vi':248,'Pa Vi':830,'Ra Vi':2368})
    assert economy.rune=='Vi'


def test_q_is_global_and_exotic_pa_pm_po_saturate_it():
    p=model.estimate({'Force':50,'Vitalité':100},{'Force':100,'Vitalité':200},'Fo')
    assert p['quality']==pytest.approx(.5)
    for stat in ('PA','PM','Portée'):
        p=model.estimate({'Force':0,stat:1},{'Force':100},'Fo')
        assert p['quality']==1


def test_pre_event_snapshot_survives_post_read_and_expires():
    from forgely_context import FusionPairing
    pair=FusionPairing()
    pair.preserve('Test',10,{'jet':{'Force':0},'pool':0})
    pair.preserve('Test',11,{'jet':{'Force':1},'pool':0})
    assert pair.take('Test',11,{'jet':{'Force':1},'pool':0})['jet']=={'Force':0}
    pair.preserve('Test',12,{'jet':{'Force':1},'pool':0})
    assert pair.take('Other',12,None) is None
    pair.preserve('Test',12,{'jet':{'Force':1},'pool':0})
    assert pair.take('Test',30,None) is None


def test_app_pairs_changed_sc_and_unchanged_sn_ec_without_losing_advice(tmp_path):
    import queue
    from types import SimpleNamespace
    from unittest.mock import Mock, patch
    from forgely import Forgely
    from forgely_context import FusionPairing, save_transition
    from forgely_workshop_readings import WorkshopReadings
    from forgely_labo_live import LiveLaboratory, compute_snapshot
    db=tmp_path/'pipeline.db'
    readings=WorkshopReadings(required_frames=2)
    readings.observe({'Force':0},0);readings.observe({'Force':0},0)
    app=SimpleNamespace(messages=queue.Queue(), workshop_readings=readings,
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        live_jet={'Force':0},live_pool=0,live_after_fusion=False,
        pending_transition=None,pre_fusion_sample=None,fusion_pairing=FusionPairing(),
        latest_observation_id=10,last_full_event_frame_id=0,last_displayed_result_frame_id=0,
        live_laboratory=LiveLaboratory(db),context_saved=0,context_rejected=0,saved_auto=0,
        status=Mock(),overlay=Mock(),atelier_info_label=Mock(),detect_label=Mock(),detect_help=Mock(),
        refresh_strategy=Mock(),render_plan=Mock(),refresh_stats_now=Mock(),
        dashboard=None,winfo_exists=lambda:False,process_messages=lambda:None)
    def persist(*args,**kwargs):return save_transition(*args,**kwargs,db_file=db)
    with patch('forgely.save_transition',side_effect=persist), \
         patch('forgely.insert_observation'),patch('forgely_dofocus.natural_profile',return_value={'Force':100}):
        for outcome in ('SC','SN','EC','EC'):
            # The post-read arrives first, matching the observer's actual queue order.
            app.messages.put(('atelier_read',({'Force':1},0)))
            app.messages.put(('auto_event_frame',(10,SimpleNamespace(rune='Fo',outcome=outcome,evidence='test'))))
            app.messages.put(('atelier_read',({'Force':1},0)))
            app.messages.put(('atelier_read',({'Force':1},0)))
            while not app.messages.empty():Forgely.process_messages(app)
            assert app.live_jet=={'Force':1} and app.live_after_fusion is False
            assert app.pending_transition is None
    snapshot=compute_snapshot(db)
    counts=[v['counts'] for v in snapshot['calibration'].values()]
    assert sum(c.get('SC',0) for c in counts)==1
    assert sum(c.get('SN',0) for c in counts)==1
    assert sum(c.get('EC',0) for c in counts)==2


def test_user_quality_is_mean_of_line_ratios_and_threshold_is_additive():
    p=model.estimate({'Force':50,'Vitalité':0},{'Force':100,'Vitalité':200},'Fo')
    assert p['quality']==pytest.approx(.25)
    p=predict(100)
    assert p['terms']['threshold']==45
    assert p['terms']['over']==69
    assert p['difficulty']==pytest.approx(5+45+69+12*86+60)
