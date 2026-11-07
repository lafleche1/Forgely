import threading
import queue
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image

class IdentityLatencyTests(unittest.TestCase):
    def test_reader_never_waits_for_complete_atelier_ocr(self):
        from forgely_item_identity import ItemIdentityReader
        image=Image.new('RGB',(1648,928),'#292040')
        icon=Image.effect_noise((32,32),60).convert('RGB')
        calls=[]
        def ocr(patch):calls.append(patch.size);return '31 40 33 Force'
        with patch('forgely_item_identity.workshop_visual_fallback',return_value=True), \
             patch('forgely_item_identity.current_icon',return_value=icon), \
             patch('forgely_item_identity.recognize_item_header',return_value=('Anneau',None,'ANNEAU')) as header:
            reader=ItemIdentityReader()
            a=reader.read(image,ocr,[(1,'Anneau')])
            b=reader.read(image.copy(),ocr,[(1,'Anneau')])
        self.assertEqual(a.known,'Anneau')
        self.assertEqual(b.signature,(('force',31,40),))
        self.assertEqual(header.call_count,1)
        self.assertEqual(len(calls),1)  # only effects needed for identity, never rune/history/recovery

    def test_changed_header_and_effects_invalidate_their_own_cache(self):
        from forgely_item_identity import ItemIdentityReader
        from forgely_item_vision import crop_item_header
        image=Image.new('RGB',(1648,928),'#292040')
        icon=Image.effect_noise((32,32),60).convert('RGB')
        with patch('forgely_item_identity.workshop_visual_fallback',return_value=True), \
             patch('forgely_item_identity.current_icon',return_value=icon), \
             patch('forgely_item_identity.recognize_item_header',return_value=('Anneau',None,'ANNEAU')) as header:
            reader=ItemIdentityReader();reader.read(image,lambda p:'31 40 33 Force',[])
            image.putpixel((300,260),(250,250,250))
            reader.read(image,lambda p:'31 40 33 Force',[])
            self.assertEqual(header.call_count,2)

    def test_gate_allows_same_frame_enrichment_but_rejects_older_frames(self):
        from forgely_item_identity import IdentityFrameGate
        gate=IdentityFrameGate();mailbox=object()
        self.assertTrue(gate.accept(mailbox,1,'A',10))
        self.assertTrue(gate.accept(mailbox,1,'A',10))
        self.assertFalse(gate.accept(mailbox,1,'A',9))
        self.assertTrue(gate.accept(mailbox,1,'A',11))
        self.assertTrue(gate.accept(mailbox,2,'A',1))
        self.assertTrue(gate.accept(object(),2,'A',1))

    def test_known_suffix_lookup_does_not_renormalize_full_catalogue_each_time(self):
        import forgely_item_vision as names
        source=('Anneau du Cycloïde','Amulette du Cycloïde')
        original=names.key_for
        with patch.object(names,'official_names',return_value=source), \
             patch.object(names,'key_for',wraps=original) as normalize:
            self.assertEqual(names.match_truncated_official_name('AU DU CYCLOÏDE'),'Anneau du Cycloïde')
            previous=normalize.call_count
            self.assertEqual(names.match_truncated_official_name('AU DU CYCLOÏDE'),'Anneau du Cycloïde')
            self.assertLessEqual(normalize.call_count-previous,1)

    def test_identity_worker_delivers_before_full_ocr_is_called(self):
        from forgely import Forgely,LatestFrameMailbox
        from forgely_performance import PerformanceTracker
        from forgely_item_identity import ItemIdentityRead
        from time import perf_counter_ns
        mailbox=LatestFrameMailbox();stop=threading.Event();messages=queue.Queue()
        icon=Image.effect_noise((32,32),60).convert('RGB')
        mailbox.publish(Image.new('RGB',(1648,928)),'A',perf_counter_ns(),0)
        app=SimpleNamespace(frame_mailbox=mailbox,stop_event=stop,messages=messages,
                            fast_preview_performance=PerformanceTracker(),_verified_item_context=None)
        reading=ItemIdentityRead('Anneau',None,'ANNEAU',icon,(('force',31,40),))
        with patch('forgely_item_identity.ItemIdentityReader.read',return_value=reading), \
             patch('forgely.item_list',return_value=[(1,'Anneau')]), \
             patch('forgely.read_atelier',side_effect=AssertionError('full OCR must not be called')):
            thread=threading.Thread(target=Forgely.item_identity_worker,args=(app,));thread.start()
            try:message=messages.get(timeout=1)
            finally:stop.set();thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        self.assertEqual(message[1][3],'identity_observation')
        self.assertEqual(message[1][4][2],'item_visual')

    def test_confirmed_empty_slot_is_not_lost_when_tracker_resets(self):
        from forgely_continuous_identity import CurrentSlotTracker
        tracker=CurrentSlotTracker()
        icon=Image.effect_noise((32,32),60).convert('RGB')
        for _ in range(3):tracker.observe(icon)
        for _ in range(3):tracker.observe(None)
        self.assertTrue(tracker.absence_confirmed)
        tracker.observe(icon)
        self.assertFalse(tracker.absence_confirmed)

    def test_same_capture_enrichment_never_increments_either_tracker_twice(self):
        from forgely_continuous_identity import CurrentSlotTracker
        from forgely_item_icons import ItemVisualTracker
        slot=CurrentSlotTracker();name=ItemVisualTracker()
        icon=Image.effect_noise((32,32),60).convert('RGB')
        token=(object(),1,'A',10)
        slot.observe(icon,frame_key=token)
        name.observe(None,icon,frame_key=token)
        slot.observe(icon,frame_key=token)
        self.assertEqual(slot.count,1)
        self.assertEqual(name.observe('Anneau',icon,frame_key=token),1)
        self.assertEqual(name.observe('Anneau',icon,frame_key=token),1)
        for frame in (11,12):
            key=(*token[:3],frame)
            slot.observe(icon,frame_key=key);name.observe('Anneau',icon,frame_key=key)
        self.assertEqual(slot.count,3);self.assertEqual(name.count,3)

    def test_failed_header_is_retried_without_waiting_for_pixel_change(self):
        from forgely_item_identity import ItemIdentityReader
        image=Image.new('RGB',(1648,928),'#292040')
        icon=Image.effect_noise((32,32),60).convert('RGB')
        with patch('forgely_item_identity.workshop_visual_fallback',return_value=True), \
             patch('forgely_item_identity.current_icon',return_value=icon), \
             patch('forgely_item_identity.monotonic',side_effect=[0,.5,1.1]), \
             patch('forgely_item_identity.recognize_item_header',side_effect=[(None,None,''),('Anneau',None,'ANNEAU')]) as header:
            reader=ItemIdentityReader()
            self.assertIsNone(reader.read(image,lambda p:'31 40 33 Force',[]).known)
            self.assertIsNone(reader.read(image,lambda p:'31 40 33 Force',[]).known)
            self.assertEqual(reader.read(image,lambda p:'31 40 33 Force',[]).known,'Anneau')
        self.assertEqual(header.call_count,2)

    def test_unresolved_fast_name_does_not_consume_full_fallback_frames(self):
        from forgely import Forgely,LatestFrameMailbox
        from forgely_performance import PerformanceTracker
        from forgely_item_identity import ItemIdentityRead
        from time import perf_counter_ns
        mailbox=LatestFrameMailbox();stop=threading.Event()
        image=Image.new('RGB',(1648,928));icon=Image.effect_noise((32,32),60).convert('RGB')
        mailbox.publish(image,'A',perf_counter_ns(),0)
        class StopOnPublish(queue.Queue):
            def put(self,item,*args,**kwargs):super().put(item,*args,**kwargs);stop.set()
        messages=StopOnPublish()
        app=SimpleNamespace(frame_mailbox=mailbox,stop_event=stop,messages=messages,
                            fast_preview_performance=PerformanceTracker(),_verified_item_context=None)
        count=0
        def read(*args):
            nonlocal count
            count+=1
            if count==1:
                mailbox.publish(image.copy(),'A',perf_counter_ns(),0)
                return ItemIdentityRead(None,None,'illisible',icon,())
            return ItemIdentityRead('Anneau',None,'ANNEAU',icon,())
        with patch('forgely_item_identity.ItemIdentityReader.read',side_effect=read), \
             patch('forgely.item_list',return_value=[]), \
             patch('forgely.match_current_item',return_value=None):
            Forgely.item_identity_worker(app)
        message=messages.get_nowait()
        self.assertEqual(count,2)
        self.assertEqual(message[1][4][3][0],'Anneau')
        self.assertTrue(messages.empty())

    def test_unreadable_static_heading_requests_a_fresh_retry_capture(self):
        from forgely import Forgely,LatestFrameMailbox
        from forgely_performance import PerformanceTracker
        from forgely_item_identity import ItemIdentityRead
        from itertools import count
        from time import perf_counter_ns
        mailbox=LatestFrameMailbox();stop=threading.Event();icon=Image.effect_noise((32,32),60).convert('RGB')
        image=Image.new('RGB',(1648,928));mailbox.publish(image,'A',perf_counter_ns(),0)
        class StopOnPublish(queue.Queue):
            def put(self,item,*args,**kwargs):super().put(item,*args,**kwargs);stop.set()
        messages=StopOnPublish()
        class CaptureRequest:
            def set(self):mailbox.publish(image.copy(),'A',perf_counter_ns(),0)
        app=SimpleNamespace(frame_mailbox=mailbox,stop_event=stop,messages=messages,confirmation_requested=CaptureRequest(),
                            fast_preview_performance=PerformanceTracker(),_verified_item_context=None)
        results=[ItemIdentityRead(None,None,'illisible',icon,()),ItemIdentityRead('Anneau',None,'ANNEAU',icon,())]
        with patch('forgely_item_identity.ItemIdentityReader.read',side_effect=results), \
             patch('forgely.match_current_item',return_value=None), \
             patch('forgely.forgely_perf_ns',side_effect=count(0,1_000_000_000)):
            thread=threading.Thread(target=Forgely.item_identity_worker,args=(app,));thread.start()
            try:message=messages.get(timeout=.7)
            finally:stop.set();thread.join(timeout=1)
        self.assertEqual(message[1][4][3][0],'Anneau')
