import sqlite3
from forgely_context import save_transition
from forgely_labo_live import LiveLaboratory, compute_snapshot
from forgely_decision import advise


def test_learning_changes_ranking_but_preserves_guards():
    jets={'Force': 20}
    baseline=advise(jets,{'Force':40},natural_max={'Force':100},pool=20)
    def learned(rune):
        return {'usable':True,'n':100,'counts':{'SC':100 if rune=='Fo' else 0,'SN':0,'EC':0 if rune=='Fo' else 100},'learning_eligible':True}
    adapted=advise(jets,{'Force':40},natural_max={'Force':100},pool=20,learning_for=learned)
    assert adapted.estimates['learning']['n']==100
    assert adapted.estimates['learning']['factor'] <= 1.2
    assert advise(jets,{'Force':40},pool=None,learning_for=learned).kind=='bloqué'
    assert 'apprentissage local' in adapted.explanation.lower()
    # A weak sample must have exactly the baseline behavior.
    weak=advise(jets,{'Force':40},natural_max={'Force':100},pool=20,
                learning_for=lambda r:{'usable':True,'learning_eligible':True,'n':2,'counts':{'SC':2}})
    assert weak.rune==baseline.rune
    assert weak.estimates['learning'] is None


def test_coherent_sessions_survive_restart_and_bad_ocr_is_excluded(tmp_path):
    db=tmp_path/'sessions.db'
    before={'jet':{'Force':20},'pool':10}
    for _ in range(30):
        save_transition('Objet','Fo','SC',before,{'jet':{'Force':21},'pool':10},db)
    save_transition('Objet','Fo','SC',before,{'jet':{'Force':19},'pool':10},db)
    result=compute_snapshot(db)
    group=next(iter(result['groups'].values()))
    assert group['n']==31  # exploratory history remains auditable
    assert group['learning_n']==30
    assert group['learning_counts']=={'SC':30,'SN':0,'EC':0}
    restarted=LiveLaboratory(db)
    restarted._snapshot=compute_snapshot(db)
    learned=restarted.learning_estimate('Objet','Fo',{'Force':20},10)
    assert learned['n']==30 and learned['learning_eligible']
    assert restarted.learning_estimate('Autre','Fo',{'Force':20},10) is None


def test_learning_reorders_comparable_runes():
    jets={'Force':20,'Intelligence':20}; targets={'Force':21,'Intelligence':21}
    bounds={'Force':100,'Intelligence':100}
    baseline=advise(jets,targets,natural_max=bounds,pool=20)
    def learned(rune):
        success=0 if rune==baseline.rune else 100
        return {'usable':True,'learning_eligible':True,'n':100,
                'counts':{'SC':success,'SN':0,'EC':100-success}}
    adapted=advise(jets,targets,natural_max=bounds,pool=20,learning_for=learned)
    assert adapted.rune!=baseline.rune
    assert advise(jets,targets,natural_max=bounds,pool=20,learning_for=learned,
                  mode='Budget optimisé',prices={'Fo':1,'Ine':100},remaining_budget=1).rune=='Fo'


def test_failed_rune_without_visible_change_is_learned(tmp_path):
    db=tmp_path/'sessions.db'
    before={'jet':{'Force':20},'pool':0}
    save_transition('Objet','Fo','EC',before,before,db,confirmed_event=True)
    group=next(iter(compute_snapshot(db)['groups'].values()))
    assert group['learning_counts']['EC']==1


def test_consistency_rejects_contradictory_results():
    from forgely_labo_live import coherent_transition
    before={'jet':{'Force':20,'Intelligence':20},'pool':10}
    assert coherent_transition('Fo','SN',before,{'jet':{'Force':21,'Intelligence':20},'pool':9})
    assert coherent_transition('Fo','EC',before,{'jet':{'Force':20,'Intelligence':20},'pool':9})
    assert not coherent_transition('Fo','SC',before,{'jet':{'Force':21,'Intelligence':19},'pool':10})
    assert not coherent_transition('Fo','SN',before,{'jet':{'Force':21,'Intelligence':20},'pool':100})
    assert not coherent_transition('Fo','SC',before,{'jet':{'Force':21},'pool':10})
