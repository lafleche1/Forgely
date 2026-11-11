import json
import tkinter as tk
import pytest


@pytest.fixture(scope='module')
def root():
    try: window=tk.Tk()
    except tk.TclError: pytest.skip('Écran Tk indisponible')
    window.withdraw()
    yield window
    if window.winfo_exists(): window.destroy()


def test_trainer_preserves_virtual_and_integrates_video_tab(root,tmp_path):
    from entrainer_forgely import TrainingWindow
    app=TrainingWindow(root,tmp_path)
    assert [app.notebook.tab(t,'text') for t in app.notebook.tabs()]==['Sessions virtuelles','Sessions vidéo']
    assert app.selected_id==14092
    assert not app.video_panel.busy
    app.video_panel.shutdown()


def test_video_panel_zone_mapping_and_persisted_settings(root,tmp_path):
    from forgely_video_ui import VideoPanel
    panel=VideoPanel(root,tmp_path)
    assert panel.relative_box((100,50),(300,150),(100,50,400,200))==(0.,0.,.5,.5)
    panel.zones['item']=(.1,.1,.5,.2)
    panel.save_layout()
    panel.shutdown()
    other=VideoPanel(root,tmp_path)
    assert other.zones['item']==[.1,.1,.5,.2]
    other.shutdown()


def test_import_dialog_uses_valid_tk_options(root,tmp_path,monkeypatch):
    from forgely_video_ui import VideoPanel
    import forgely_video_ui
    calls=[]
    def choose(**kwargs):
        assert 'text' not in kwargs
        calls.append(kwargs)
        return ()
    monkeypatch.setattr(forgely_video_ui.filedialog,'askopenfilenames',choose)
    panel=VideoPanel(root,tmp_path);panel.add_files();assert calls
    panel.shutdown()


def test_review_edit_requalifies_without_silently_accepting_ambiguous_events(root,tmp_path):
    from forgely_video_ui import VideoPanel
    from test_video_store import event
    panel=VideoPanel(root,tmp_path)
    panel.session={'id':'a'*64,'events':[event()],'status':'done','path':'test.mp4'}
    panel.apply_review('e1',{'status':'rejected','review_note':'illisible'})
    assert panel.session['events'][0]['status']=='rejected'
    assert panel.session['events'][0]['reviewed_at']
    assert panel.store.load_session('a'*64)['events'][0]['review_note']=='illisible'
    panel.shutdown()


def test_review_resolves_rune_ambiguity_but_not_multiple_events(root,tmp_path):
    from forgely_video_ui import VideoPanel
    from forgely_video_store import qualify_event
    from test_video_store import event
    panel=VideoPanel(root,tmp_path);e=event();e['issues']=['ambiguous_rune']
    panel.session={'id':'a'*64,'events':[e],'status':'done','path':'test.mp4'}
    panel.apply_review('e1',{'rune':'Ga Pa','status':'confirmed'})
    assert qualify_event(panel.session['events'][0])['eligible']
    e['issues']=['multiple_events','ambiguous_rune']
    panel.apply_review('e1',{'rune':'Ga Pa','status':'confirmed'})
    assert not qualify_event(panel.session['events'][0])['eligible']
    panel.shutdown()


def test_review_fields_keep_unknown_values_distinct_from_zero():
    from forgely_video_ui import snapshot_from_fields
    assert snapshot_from_fields({'PA':'0','Force':''},'')=={'jet':{'PA':0},'pool':None}
    assert snapshot_from_fields({'Force':'40'},'2,5')['pool']==2.5
    with pytest.raises(ValueError):snapshot_from_fields({'PA':'nan'},'0')
