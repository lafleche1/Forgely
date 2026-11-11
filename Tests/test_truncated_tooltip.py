import queue
import threading
from types import SimpleNamespace
from unittest.mock import Mock,patch

import pytest
from PIL import Image,ImageDraw

from forgely_atelier import effects_text_occluded


FIELD_TEXT='''Effets / Carac. #19
2%
© 1 Portée
POIDS 5
Ÿ -15 Force PRIX MO
% -15 Intelligence °U NT:1
QUANTIT
@ -15 Chance QUANTIT
. Cette amt
& -15 Agilité d'une peti
aucune lin
6 Optior'''


@pytest.mark.parametrize('text', [FIELD_TEXT,'40 Force\nPoids 5',
    '40 Force\nPRIX MO\nQUANTIT','1 PA\nPRIX MOY\nQUANTITÉ',
    '0 Tacle\npoids:10','-15 Force\nQUANTIT EN INVEN'])
def test_truncated_item_tooltip_is_not_a_workshop_jet(text):
    assert effects_text_occluded(text)


@pytest.mark.parametrize('text', ['1 Portée\n-15 Force\n-15 Intelligence\n-15 Chance\n-15 Agilité',
    '0 PA\n0 Tacle\n0 Force','40 Force\n5 Dommages Feu\n100 Pods',
    'Effets / Carac.\n300 Vitalité\n30 Puissance'])
def test_normal_effects_do_not_become_tooltips(text):
    assert not effects_text_occluded(text)


def test_observer_discards_contaminated_current_zone_and_emits_no_numbers():
    from forgely import Forgely,LatestFrameMailbox
    from forgely_pipeline import VerifiedItemContext
    from forgely_zone_cache import ZoneCache
    image=Image.new('RGB',(1648,928),'#38394e')
    icon=image.resize((32,32));ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    mailbox=LatestFrameMailbox();mailbox.publish(image,'DOFUS',1,0)
    app=Mock();app.frame_mailbox=mailbox;app.stop_event=threading.Event()
    app.capture=Mock(last_handle=123,manual_handle=None)
    class Messages(queue.Queue):
        def put(self,message,*args,**kwargs):
            super().put(message,*args,**kwargs)
            if message[0]=='worker_message' and message[1][3]=='atelier_masked':app.stop_event.set()
    app.messages=Messages();app.capture_debug_requested=threading.Event()
    app._confirmed_atelier_read=None
    app._verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'known',icon,())
    app.active_equipment_verified=True;app.item.get.return_value='known'
    app.completed_ocr_attempts=0;app._ocr_stale_frames=0
    app.occluded_observations=0;app._occluded_frames_rejected=0
    contaminated=SimpleNamespace(active=True,readable=True,effects=FIELD_TEXT,reliquat='reliquat : 0',
        history='',runes='',title='Joaillomager',reason='',timings={},recovery_pending=False)
    cache=ZoneCache();cache.remember('current_jet',image,FIELD_TEXT)
    cache.confirm_numeric(tuple(cache.entries.items()))
    def read(*args,**kwargs):
        kwargs['on_numeric'](contaminated)
        return contaminated
    with patch('forgely.read_atelier',side_effect=read), \
         patch('forgely.ZoneCache',return_value=cache), \
         patch('forgely.current_icon',return_value=icon):
        Forgely.observer_worker(app)
    kinds=[]
    while not app.messages.empty():
        message=app.messages.get_nowait()
        if message[0]=='worker_message':
            kind,data=message[1][3:]
            kinds.append(data[2] if kind=='observation' else kind)
    assert 'atelier_masked' in kinds
    assert 'atelier_read' not in kinds
    assert app.occluded_observations==1
    assert 'current_jet' not in cache.entries
    assert 'current_jet' not in cache.confirmed_numeric
