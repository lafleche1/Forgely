from pathlib import Path
from PIL import Image
import pytest
from forgely_history_reader import HistoryReader

FIXTURES=Path(__file__).parent/'fixtures/history_unity_20261109'


def growing_history():
    image=Image.open(FIXTURES/'151219.png').convert('RGB')
    first=image.crop((0,0,246,34));last=image.crop((0,34,246,63))
    old=Image.new('RGB',(246,170),(56,59,84))
    old.paste(first,(0,0));old.paste(first,(0,34))
    new=old.copy();new.paste(last,(0,68))
    return old,new


@pytest.mark.parametrize('stamp,outcomes,changes,pool',[
    ('142129',['SC'],[{'Dommages Terre':1}],[0]),
    ('142203',['SN'],[{'Initiative':10,'Intelligence':-1}],[0]),
    ('142224',['SN'],[{'Dommages Feu':-2,'% Résistance Eau':1}],[1]),
    ('150921',['SN'],[{'Force':3}],[-1]),
    ('151032',['EC'],[{'Force':-2}],[-1]),
    ('151219',['SC','EC'],[{'Intelligence':1},{}],[0,-1]),
    ('151301',['SN'],[{'Vitalité':-2,'Intelligence':-3,'% Résistance Eau':1}],[-1]),
    ('151453',['SN'],[{'Dommages Feu':-1,'% Résistance Eau':1,'Esquive PM':-1}],[1]),
    ('151555',['EC'],[{'% Résistance Eau':-1}],[1]),
    ('151840',['EC','EC'],[
        {'Vitalité':-2,'Intelligence':-9,'Dommages Feu':-3,'Esquive PM':-2,'% Résistance Eau':-1},
        {'Vitalité':-16,'Intelligence':-11}],[-1,-1]),
])
def test_user_captures_recognize_unsigned_gains_and_colored_outcomes(stamp,outcomes,changes,pool):
    groups=HistoryReader().read(Image.open(FIXTURES/f'{stamp}.png'))
    assert [g.outcome for g in groups]==outcomes
    assert [g.changes for g in groups]==changes
    assert [g.pool_direction for g in groups]==pool


def test_unchanged_pixels_do_not_launch_ocr_again():
    calls=[]
    def ocr(image):
        calls.append(image.size)
        return '3 Force\n- reliquat'
    reader=HistoryReader(ocr=ocr)
    picture=Image.open(FIXTURES/'150921.png')
    before=picture.tobytes()
    a=reader.read(picture);b=reader.read(picture.copy())
    assert a==b
    assert len(calls)==1
    assert picture.tobytes()==before


def test_missing_stat_or_conflicting_color_abstains():
    reader=HistoryReader(ocr=lambda image:'mots illisibles\n- reliquat')
    assert reader.read(Image.open(FIXTURES/'150921.png'))[0].outcome is None


def test_live_history_adapter_confirms_only_a_new_group_and_its_selected_rune():
    from forgely_history_reader import VisualHistoryTracker
    # Use real SC + EC crops to build growing history, latest at the bottom.
    old,new=growing_history()
    tracker=VisualHistoryTracker()
    assert tracker.observe(old,'item',1,'Ine').event is None
    assert tracker.observe(old,'item',2,'Ine').event is None
    assert tracker.observe(new,'item',3,'Ine').event is None
    result=tracker.observe(new,'item',4,'Ine')
    assert result.event.outcome=='EC'
    assert result.event.rune=='Ine'
    assert tracker.observe(new,'item',5,'Ine').event is None
    # Context switch only establishes a new baseline, never counts old history.
    assert tracker.observe(new,'other',6,'Ine').event is None


def test_rune_change_during_new_history_cannot_train_a_failure():
    from forgely_history_reader import VisualHistoryTracker
    old,new=growing_history()
    t=VisualHistoryTracker()
    t.observe(old,'item',1,'Ine');t.observe(old,'item',2,'Ine')
    t.observe(new,'item',3,'Pa Ine')
    result=t.observe(new,'item',4,'Pa Ine')
    assert result.event is None or result.event.rune is None


def test_full_user_history_keeps_every_continuation_outside_scrollbar():
    patch=Image.open(FIXTURES/'151702.png').crop((260,283,520,898))
    groups=HistoryReader().read(patch)
    # First group is the clipped equipment heading, never an outcome.
    assert groups[0].outcome is None
    assert [g.outcome for g in groups[1:]]==['EC','SC','EC','SN','SC','SN','SC','SN','EC']


@pytest.mark.parametrize('wrong', [False,True])
def test_visual_learning_requires_history_deltas_to_match_before_and_after(wrong):
    from forgely_detection import Observation
    from forgely_learning import FusionContextTracker
    event=Observation('Fo','SN','3 Force','visuel',changes={'Force':1},pool_direction=-1,visual=True)
    t=FusionContextTracker()
    old='Anneau\nréussite critique a\nréussite critique b'
    new='Anneau\nréussite neutre c\nréussite critique a\nréussite critique b'
    for _ in range(2):t.observe('item',old,{'Force':10,'Intelligence':20},5,None)
    after={'Force':11,'Intelligence':19 if wrong else 20}
    t.observe('item',new,after,4,event)
    result=t.observe('item',new,after,4,None)
    assert (result is None)==wrong
