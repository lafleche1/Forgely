from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from PIL import Image, ImageDraw
from forgely_attempt_groups import AttemptGroupTracker, extract_attempt_groups
FIXTURE=Path(__file__).parent/'fixtures/attempt_groups/history_215556.png'

def picture(labels):
    source=Image.open(FIXTURE).convert('RGB')
    im=Image.new('RGB',source.size,(56,59,84))
    im.paste(source.crop((0,0,232,30)),(0,0))
    icon=source.crop((2,42,26,54))
    draw=ImageDraw.Draw(im)
    for i,label in enumerate(labels):
        y=42+i*55
        im.paste(icon,(2,y))
        draw.text((35,y),label,fill='white')
        draw.text((50,y+18),'- reliquat',fill='white')
    return im

def stable(t,im,context='a',start=1):
    t.observe(im,context,start)
    return t.observe(im,context,start+1)

def test_real_two_icons_not_three_text_rows():
    groups=extract_attempt_groups(Image.open(FIXTURE))
    assert len(groups)==2
    assert groups[1].evidence.height>groups[0].evidence.height
    assert groups[0].root_signature==groups[1].root_signature

def test_initial_reference_and_duplicate_frame_never_emit():
    t=AttemptGroupTracker(); im=picture(['old-a','old-b'])
    assert not t.observe(im,'a',1)['newly_confirmed_groups']
    assert t.observe(im,'a',1)['status']=='duplicate_frame'
    assert not t.observe(im,'a',2)['newly_confirmed_groups']
    assert not t.observe(im,'a',3)['newly_confirmed_groups']

def test_new_group_once_with_continuations():
    t=AttemptGroupTracker(); stable(t,picture(['old-a','old-b']))
    new=picture(['new','old-a','old-b'])
    assert t.observe(new,'a',3)['pending']
    r=t.observe(new,'a',4)
    assert len(r['newly_confirmed_groups'])==1
    assert r['observed_attempts']==1
    assert r['newly_confirmed_groups'][0].outcome is None
    assert not t.observe(new,'a',5)['newly_confirmed_groups']

def test_scroll_clipping_and_jitter_abstain():
    t=AttemptGroupTracker(); stable(t,picture(['old-a','old-b']))
    assert not stable(t,picture(['new','old-a']),start=3)['newly_confirmed_groups']
    assert not stable(t,picture(['old-a','changed-b']),start=5)['newly_confirmed_groups']

def test_context_reset_ignores_existing_groups():
    t=AttemptGroupTracker(); stable(t,picture(['a','b']))
    assert not stable(t,picture(['new','a','b']),context='other',start=3)['newly_confirmed_groups']

def test_identical_repeated_groups_are_ambiguous():
    t=AttemptGroupTracker(); stable(t,picture(['same','same']).crop((0,0,232,138)))
    assert not stable(t,picture(['same','same','same']).crop((0,0,232,193)),start=3)['newly_confirmed_groups']

def test_continuation_change_is_not_new_attempt():
    t=AttemptGroupTracker(); old=picture(['a','b']); stable(t,old)
    changed=old.copy(); ImageDraw.Draw(changed).text((50,132),'-1 Force',fill='red')
    r=stable(t,changed,start=3)
    assert r['status']=='ambiguous_reference'
    assert not r['newly_confirmed_groups']

def test_real_fixture_initial_baseline_does_not_count_old_attempts():
    t=AttemptGroupTracker(); r=stable(t,Image.open(FIXTURE))
    assert len(r['visible_groups'])==2
    assert r['observed_attempts']==0
    assert not r['newly_confirmed_groups']

def test_missing_anchor_resets_reference():
    t=AttemptGroupTracker(); stable(t,picture(['a','b']))
    t.observe(Image.new('RGB',(232,562),(56,59,84)),'a',3)
    assert not stable(t,picture(['new','a','b']),start=4)['newly_confirmed_groups']

def test_bottom_clipped_history_window_never_counts_insertions():
    t=AttemptGroupTracker()
    old=picture(['a','b']).crop((0,0,232,124))
    new=picture(['new','a','b']).crop((0,0,232,179))
    # A group continuation touches the bottom edge in both windows.
    stable(t,old)
    r=stable(t,new,start=3)
    assert r['status']=='clipped_window'
    assert not r['newly_confirmed_groups']
    assert r['observed_attempts']==0

def test_identical_groups_can_grow_in_complete_window_with_blank_tail():
    t=AttemptGroupTracker(); stable(t,picture(['same','same']))
    r=stable(t,picture(['same','same','same']),start=3)
    assert r['status']=='new_groups_confirmed'
    assert len(r['newly_confirmed_groups'])==1

def test_visible_scrollbar_abstains_even_with_blank_tail():
    t=AttemptGroupTracker(); old=picture(['a','b'])
    ImageDraw.Draw(old).rectangle((226,40,230,220),fill=(110,110,130))
    r=stable(t,old)
    assert r['status']=='scrollbar_visible'
    new=picture(['new','a','b'])
    ImageDraw.Draw(new).rectangle((226,40,230,220),fill=(110,110,130))
    assert not stable(t,new,start=3)['newly_confirmed_groups']
