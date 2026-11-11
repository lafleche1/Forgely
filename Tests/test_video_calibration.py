from test_video_store import event
from forgely_video_store import transfer_session
from forgely_labo_live import compute_snapshot, LiveLaboratory


def test_video_only_database_calibrates_exact_context_and_retracts(tmp_path):
    db=tmp_path/'observations.sqlite'
    session={'id':'a'*64, 'events':[event()]}
    transfer_session(session,db)
    snapshot=compute_snapshot(db,minimum=1)
    key=('Gelano','Ga Pa',17.,(('PA',0),))
    assert snapshot['calibration'][key]['counts']=={'SC':1}
    assert snapshot['video_observations']==1
    live=LiveLaboratory(db,minimum=1)
    assert live.refresh_if_changed()
    assert live.calibration('Gelano','Ga Pa',{'PA':0},17)['counts']=={'SC':1}
    session['events'][0]['status']='rejected'
    transfer_session(session,db)
    assert live.refresh_if_changed()
    assert live.calibration('Gelano','Ga Pa',{'PA':0},17) is None


def test_live_screen_and_video_counts_combine_without_losing_provenance(tmp_path):
    from forgely_context import save_transition
    db=tmp_path/'observations.sqlite'
    e=event()
    save_transition('Gelano','Ga Pa','SC',e['before'],e['after'],db,
                    event_confirmed=True,natural_max={'PA':1},complete=True)
    transfer_session({'id':'a'*64,'events':[e]},db)
    snapshot=compute_snapshot(db,minimum=1)
    key=('Gelano','Ga Pa',17.,(('PA',0),))
    assert snapshot['calibration'][key]['counts']=={'SC':2}
    assert snapshot['video_observations']==1


def test_reports_escape_raw_content_and_disclose_limits(tmp_path):
    from forgely_video_report import write_report
    e=event();e['raw']={'history':'<script>alert(1)</script>'}
    session={'id':'a'*64,'path':'<script>.mp4','events':[e],'status':'done',
             'info':{'duration':12},'boundaries':[],'cursor':11.5}
    path=write_report(session,tmp_path)
    html=path.read_text(encoding='utf-8')
    assert '<script>' not in html
    assert 'SC' in html and 'Gelano' in html and 'audio' in html
    assert (tmp_path/'rapport.json').is_file() and (tmp_path/'tentatives.csv').is_file()
    import json
    result=json.loads((tmp_path/'rapport.json').read_text(encoding='utf-8'))
    assert result['by_item']['Gelano']['runes']=={'Ga Pa':1}
    assert result['by_item']['Gelano']['rune_density']==100
