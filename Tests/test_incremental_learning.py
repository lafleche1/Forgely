from forgely_context import save_transition
from forgely_labo_live import LiveLaboratory

BEFORE={'jet':{'Force':20,'Vitalité':290},'pool':5}
AFTER={'jet':{'Force':21,'Vitalité':290},'pool':5}


def test_new_attempt_is_available_synchronously_and_survives_restart(tmp_path):
    db=tmp_path/'contexts.db'
    lab=LiveLaboratory(db)
    save_transition('Anneau','Fo','SC',BEFORE,AFTER,db,event_confirmed=True)
    assert lab.refresh()==1
    assert lab.estimate('Anneau','Fo',BEFORE['jet'],5)['n']==1
    result=lab.experience('Anneau','Fo',BEFORE['jet'],5,{'Force':40},{'Force':(1,40),'Vitalité':(1,300)})
    assert result['n']==1
    assert lab.refresh()==0
    assert lab.status()['observations']==1
    second=LiveLaboratory(db);second.refresh()
    assert second.estimate('Anneau','Fo',BEFORE['jet'],5)['n']==1


def test_incremental_refresh_counts_only_new_rows_and_is_thread_safe(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    db=tmp_path/'contexts.db';lab=LiveLaboratory(db)
    for _ in range(3):save_transition('Anneau','Fo','SC',BEFORE,AFTER,db,event_confirmed=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(lambda _:lab.refresh(),range(2)))
    assert sum(results)==3
    assert lab.estimate('Anneau','Fo',BEFORE['jet'],5)['n']==3
    save_transition('Anneau','Fo','EC',BEFORE,BEFORE,db,event_confirmed=True)
    assert lab.refresh()==1
    assert lab.estimate('Anneau','Fo',BEFORE['jet'],5)['counts']=={'SC':3,'EC':1}


def test_impossible_legacy_post_state_is_excluded_from_exact_counts_too(tmp_path):
    db=tmp_path/'contexts.db';lab=LiveLaboratory(db)
    save_transition('Anneau','Fo','SC',BEFORE,
        {'jet':{'Force':21,'Vitalité':300},'pool':5},db,event_confirmed=True)
    assert lab.refresh()==0
    assert lab.status()['rejected']==1
    assert lab.estimate('Anneau','Fo',BEFORE['jet'],5) is None
