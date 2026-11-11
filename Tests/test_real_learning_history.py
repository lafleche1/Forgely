from pathlib import Path
from PIL import Image
from forgely_history_reader import VisualHistoryTracker


def confirmed_video_transition():
    tracker=VisualHistoryTracker()
    root=Path(__file__).parent
    results=[]
    for i in range(4):
        results.append(tracker.observe(Image.open(root/f'learning-{i}.png'),'same slot',i))
    assert tracker.tracker._init_count>=2
    assert results[0].event is None
    assert results[1].event is None
    assert results[2].event is None
    assert results[3].event is not None
    assert results[3].event.rune=='Ré Per Eau'
    assert results[3].event.outcome=='SN'
    assert results[3].event.changes=={'Dommages Neutre':-1,'Initiative':-7,'% Résistance Eau':1}
    assert tracker.observe(Image.open(root/'learning-3.png'),'same slot',4).event is None
    return results


def test_real_video_pixel_variations_do_not_reset_semantic_confirmation():
    confirmed_video_transition()


def test_verified_item_history_scope_survives_incidental_icon_pixels():
    from forgely_pipeline import history_scope
    icon=Image.new('RGB',(32,32),'red');other=icon.copy();other.putpixel((4,5),(254,0,0))
    mailbox=object()
    assert history_scope(mailbox,1,'DOFUS','verified item',icon)==history_scope(mailbox,1,'DOFUS','verified item',other)
    assert history_scope(mailbox,1,'DOFUS','verified item',icon)!=history_scope(mailbox,1,'DOFUS','other item',icon)
    assert history_scope(mailbox,1,'DOFUS',None,icon)!=history_scope(mailbox,1,'DOFUS',None,other)


def test_confirmed_video_result_reaches_persistent_real_learning(tmp_path):
    from forgely_learning import FusionContextTracker,complete_learning_profile
    from forgely_context import save_transition
    from forgely_labo_live import LiveLaboratory
    item='Anneau du Cycloïde'
    natural=complete_learning_profile(item)
    before=dict(natural);before.update({'Dommages Neutre':8,'Initiative':168,'% Résistance Eau':0})
    after=dict(before);after.update({'Dommages Neutre':7,'Initiative':161,'% Résistance Eau':1})
    tracker=FusionContextTracker();transition=None
    for i,result in enumerate(confirmed_video_transition()):
        post=i>=2
        transition=tracker.observe(item,result.history,after if post else before,
                                   4.4 if post else 4.7,result.event,event_frame_id=i) or transition
    assert transition is not None
    database=tmp_path/'learning.sqlite3'
    save_transition(item,transition['rune'],transition['outcome'],transition['before'],transition['after'],
                    db_file=database,event_confirmed=True,natural_max=natural,complete=True)
    laboratory=LiveLaboratory(db_file=database)
    laboratory.refresh_if_changed()
    assert laboratory.status()['observations']==1
    assert laboratory.empirical_model().sample_count==1
    experience=laboratory.experience(item,'Ré Per Eau',before,4.7,natural,natural)
    assert experience['n']==1
    assert experience['factor']!=1
