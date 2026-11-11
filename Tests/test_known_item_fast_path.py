import queue,threading
from types import SimpleNamespace
from unittest.mock import patch,Mock
from PIL import Image,ImageDraw


def test_confirmed_icon_does_not_require_new_catalogue_search_after_row_changes():
    from forgely import Forgely,LatestFrameMailbox
    from forgely_continuous_identity import CurrentSlotTracker
    from forgely_pipeline import VerifiedItemContext
    icon=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    tracker=CurrentSlotTracker()
    for _ in range(3):tracker.observe(icon)
    frames=[]
    for i in range(2):
        im=Image.new('RGB',(1648,928),'#333333')
        ImageDraw.Draw(im).rectangle((490,300,590,320),fill='red' if i else 'green')
        frames.append((0,(i+1,im,'DOFUS',1,0)))
    stop=threading.Event();mailbox=LatestFrameMailbox()
    def next_frame(*args):
        if frames:return frames.pop(0)
        stop.set();return 0,None
    app=SimpleNamespace(stop_event=stop,frame_mailbox=mailbox,messages=queue.Queue(),
                        active_equipment_verified=True,current_slot_tracker=tracker,
                        fast_preview_performance=Mock(),
                        _verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'known item',icon,()))
    with patch.object(mailbox,'wait_snapshot',side_effect=next_frame), \
         patch('forgely.current_icon',return_value=icon), \
         patch('forgely_item_identity.ItemIdentityReader') as reader:
        Forgely.item_identity_worker(app)
    reader.return_value.read.assert_not_called()
