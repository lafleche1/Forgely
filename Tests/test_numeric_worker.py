import queue,threading
from types import SimpleNamespace
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from forgely import Forgely,LatestFrameMailbox
from forgely_atelier import read_atelier,crop_zone,focus_workshop,choose_reliquat
from forgely_jet import parse_jet
from forgely_workshop_layout import WorkshopLocator
from forgely_ocr_backend import extract_text
from forgely_pipeline import VerifiedItemContext
import pytest


def test_numeric_only_mode_never_reads_history_or_modifications():
    image=Image.new('RGB',(1648,928),'#38394e')
    def ocr(patch):
        if patch.size==crop_zone(image,'current_jet').size:return '1 PA'
        if patch.size==crop_zone(image,'reliquat').size:return 'reliquat : 88'
        raise AssertionError('Secondary zone requested by numeric-only reader')
    with patch('forgely_atelier.workshop_visual_fallback',return_value=True):
        result=read_atelier(image,ocr,title_cache={},five_zones=True,numeric_only=True)
    assert parse_jet(result.effects)=={'PA':1}
    assert choose_reliquat(result.effects,result.reliquat)==88
    assert result.history==result.modifications==''


def test_latest_user_capture_via_real_normalization_reads_pa_zero_and_pool_88():
    image=Image.open(Path(__file__).parent/'fixtures/kido_zero_pa_212821.png')
    image=focus_workshop(WorkshopLocator().normalize(image,'new-capture'))
    result=read_atelier(image,extract_text,title_cache={},five_zones=True,numeric_only=True)
    assert parse_jet(result.effects)['PA']==0
    assert choose_reliquat(result.effects,result.reliquat)==88


def test_worker_advances_across_frames_without_waiting_for_history():
    image=Image.new('RGB',(1648,928),'#38394e')
    from PIL import ImageDraw
    icon=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    mailbox=LatestFrameMailbox();mailbox.publish(image,'DOFUS',1,0)
    stop=threading.Event();delivered=threading.Event();events=[]
    class Messages(queue.Queue):
        def put(self,message,*a,**kw):
            super().put(message,*a,**kw)
            if message[0]=='worker_message' and message[1][3]=='observation':
                events.append(message[1][4]);delivered.set()
    app=SimpleNamespace(frame_mailbox=mailbox,stop_event=stop,capture=SimpleNamespace(last_handle=123),
        messages=Messages(),active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Kido'),
        _verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'Kido',icon,()),
        pool_refresh_requested=threading.Event(),confirmation_requested=threading.Event())
    def ocr(p):
        if p.size==crop_zone(image,'current_jet').size:return '0 PA'
        if p.size==crop_zone(image,'reliquat').size:return 'reliquat : 88'
        raise AssertionError('History must stay outside numeric worker')
    with patch('forgely.current_icon',return_value=icon),patch('forgely.extract_text',side_effect=ocr),\
         patch('forgely_atelier.workshop_visual_fallback',return_value=True),ThreadPoolExecutor(max_workers=1) as worker:
        job=worker.submit(Forgely.numeric_worker,app)
        try:
            assert delivered.wait(3),getattr(app,'numeric_worker_error','no delivery')
            delivered.clear();mailbox.publish(image,'DOFUS',2,0)
            assert delivered.wait(3)
            assert events[0][0]!=events[1][0]
            assert all(e[3][:2]==({'PA':0},88) for e in events)
            assert all(e[3][2].complete is False for e in events)
        finally:stop.set()
        job.result(timeout=3)


def test_worker_drops_a_read_if_capture_generation_changes_during_ocr():
    from PIL import ImageDraw
    image=Image.new('RGB',(1648,928),'#38394e')
    icon=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    mailbox=LatestFrameMailbox();mailbox.publish(image,'DOFUS',1,0)
    stop=threading.Event();entered=threading.Event();release=threading.Event()
    app=SimpleNamespace(frame_mailbox=mailbox,stop_event=stop,capture=SimpleNamespace(last_handle=123),
        messages=queue.Queue(),active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Kido'),
        _verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'Kido',icon,()),
        pool_refresh_requested=threading.Event(),confirmation_requested=threading.Event())
    def ocr(p):
        entered.set();assert release.wait(3)
        return '0 PA' if p.size==crop_zone(image,'current_jet').size else 'reliquat : 88'
    with patch('forgely.current_icon',return_value=icon),patch('forgely.extract_text',side_effect=ocr),\
         patch('forgely_atelier.workshop_visual_fallback',return_value=True),ThreadPoolExecutor(max_workers=1) as worker:
        job=worker.submit(Forgely.numeric_worker,app)
        try:
            assert entered.wait(3)
            mailbox.invalidate('account changed');stop.set();release.set()
        finally:stop.set();release.set()
        job.result(timeout=3)
    assert app.messages.empty()


@pytest.mark.parametrize('failure', ['hidden', 'error', 'missing_pool'])
def test_forced_pool_read_survives_an_unsuccessful_numeric_frame(failure):
    image=Image.new('RGB',(1648,928),'#38394e')
    icon=Image.effect_noise((32,32),50).convert('RGB')
    mailbox=LatestFrameMailbox();mailbox.publish(image,'DOFUS',1,0)
    stop=threading.Event();request=threading.Event();request.set()
    app=SimpleNamespace(frame_mailbox=mailbox,stop_event=stop,
        capture=SimpleNamespace(last_handle=123),messages=queue.Queue(),
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Kido'),
        _verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'Kido',icon,()),
        pool_refresh_requested=request,confirmation_requested=threading.Event())
    frames=[(0,(i,image,'DOFUS',1,0)) for i in (1,2)]
    tokens=[]
    def next_frame(*args):
        if frames:return frames.pop(0)
        stop.set();return 0,None
    def read(*args,**kwargs):
        tokens.append(kwargs['pool_ocr_token'])
        if len(tokens)==1 and failure=='error':raise RuntimeError('temporary OCR failure')
        return SimpleNamespace(active=not(len(tokens)==1 and failure=='hidden'),
            effects='0 PA',reliquat='' if len(tokens)==1 and failure=='missing_pool' else 'reliquat : 88',
            timings={})
    with patch.object(mailbox,'wait_snapshot',side_effect=next_frame), \
         patch('forgely.current_icon',return_value=icon),patch('forgely.read_atelier',side_effect=read):
        Forgely.numeric_worker(app)
    assert tokens==[(id(mailbox),0,1),(id(mailbox),0,2)]
    assert not request.is_set()
    message=app.messages.get_nowait()
    assert message[1][4][3][:2]==({'PA':0},88)
    assert app.messages.empty()
