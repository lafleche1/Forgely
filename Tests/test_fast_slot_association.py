from PIL import Image,ImageDraw


def artwork(color):
    image=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(image).ellipse((4,4,27,27),fill=color)
    return image


def test_three_fast_frames_can_prime_one_ocr_identity_check():
    from forgely_continuous_identity import RapidSlotTracker,CurrentSlotTracker,prime_slot_tracker
    fast=RapidSlotTracker();icon=artwork('red')
    context=(object(),1,'DOFUS')
    for stamp in (100,200,300):evidence=fast.observe(icon,context,stamp)
    slow=CurrentSlotTracker()
    assert prime_slot_tracker(slow,evidence,icon,context,400)
    assert slow.observe(icon,())[0]


def test_fast_association_rejects_stale_other_context_and_other_icon():
    from forgely_continuous_identity import RapidSlotTracker,CurrentSlotTracker,prime_slot_tracker
    fast=RapidSlotTracker();icon=artwork('red')
    context=(object(),1,'DOFUS')
    for stamp in (100,200,300):evidence=fast.observe(icon,context,stamp)
    for ctx,other,now in [(context,icon,3_000_000_000),
                          ((context[0],2,'DOFUS'),icon,400),
                          (context,artwork('blue'),400)]:
        slow=CurrentSlotTracker()
        assert not prime_slot_tracker(slow,evidence,other,ctx,now)
        assert slow.count==0
    assert fast.observe(None,context,500) is None

