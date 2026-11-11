from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image
from forgely_fast_preview import FastRunePreview
from forgely_history_reader import VisualHistoryRead


def test_old_history_does_not_keep_invalidating_a_correct_jet():
    preview=FastRunePreview(('Fo',))
    image=Image.new('RGB',(1648,928),'#38394e')
    group=SimpleNamespace(outcome='SN',changes={'Force':1})
    with patch('forgely_fast_preview.workshop_visual_fallback',return_value=True), \
         patch('forgely_fast_preview.current_icon',return_value=image.resize((32,32))), \
         patch.object(preview.visual,'observe',return_value=VisualHistoryRead((group,),'old history')):
        for _ in range(4):
            reading=preview.read(image,'DOFUS',Mock())
            assert not reading.event
            assert not reading.changes
