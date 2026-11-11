from PIL import Image
from unittest.mock import patch,Mock
from types import SimpleNamespace
import queue
import pytest
import forgely_jet as jet


def test_first_row_live_recovery_is_bounded_and_resumes_without_replaying_ocr():
    jet._FIRST_ROW_FAILURES.clear();jet._FIRST_ROW_SUCCESSES.clear()
    image=Image.new('RGB',(330,420),'#312940')
    with patch('pytesseract.image_to_string',side_effect=['']*4+['342 Vitalité']) as ocr:
        for _ in range(3):
            before=ocr.call_count
            found=jet.read_first_effect_row_live(image)
            assert ocr.call_count-before<=2
        assert found=='342 Vitalité'
        assert ocr.call_count==5


def test_early_workshop_notice_does_not_enable_advice_or_accept_old_sessions():
    from forgely import Forgely,LatestFrameMailbox
    mailbox=LatestFrameMailbox();mailbox.publish(Image.new('RGB',(1648,928)),'Dofus',1,0)
    app=SimpleNamespace(messages=queue.Queue(),frame_mailbox=mailbox,
        detect_label=Mock(),detect_help=Mock(),overlay=Mock(),workshop_active=False,
        refresh_strategy=Mock(),winfo_exists=lambda:False)
    app.messages.put(('workshop_detected',(mailbox,mailbox.generation(),'Dofus')))
    Forgely.process_messages(app)
    assert app.detect_label.configure.called
    assert app.workshop_active is True
    app.refresh_strategy.assert_called()
    app.observation_only=False;app.active_equipment_verified=False;app.plan=None
    with patch('forgely.read_settings',return_value={}):
        assert Forgely._strategy_current(app).rune is None
    app.detect_label.reset_mock()
    app.messages.put(('workshop_detected',(mailbox,mailbox.generation()+1,'Dofus')))
    Forgely.process_messages(app)
    assert not app.detect_label.configure.called


def test_artwork_only_identity_does_not_read_history_names_or_table_ocr():
    from forgely_item_identity import ItemIdentityReader
    from forgely_equipment_identity import IdentityDecision
    image=Image.new('RGB',(1648,928),'#312940')
    with patch('forgely_item_identity.workshop_visual_fallback',return_value=True), \
         patch('forgely_item_identity.current_icon',return_value=Image.new('RGB',(32,32),'red')), \
         patch('forgely_item_identity.slot_equipment_decision',return_value=IdentityDecision('Anneau du Cycloïde',(),'slot_artwork_sparse_bounds')):
        result=ItemIdentityReader(artwork_only=True).read(image,lambda _:pytest.fail('Unnecessary OCR'),[])
    assert result.known=='Anneau du Cycloïde'
    assert result.signature==()


def test_five_zone_reader_does_not_ocr_inventory_or_minmax_columns():
    from forgely_atelier import read_atelier,crop_zone
    image=Image.new('RGB',(1648,928),'#312940')
    sizes=[]
    def ocr(patch):
        sizes.append(patch.size)
        return '58 Agilité\n30 Sagesse\n6% Critique' if patch.size==crop_zone(image,'current_jet').size else 'reliquat : 0'
    with patch('forgely_atelier.workshop_visual_fallback',return_value=True):
        result=read_atelier(image,ocr,title_cache={},five_zones=True)
    assert result.active
    assert crop_zone(image,'effects').size not in sizes
    assert crop_zone(image,'runes').size not in sizes
    assert result.runes==''
    assert jet.parse_jet(result.effects)['Coups Critiques']==6


def test_real_current_padgref_is_not_named_after_old_cycloid_history():
    from pathlib import Path
    from forgely_workshop_layout import WorkshopLocator
    from forgely_item_identity import ItemIdentityReader
    image=Image.open(Path(__file__).parent/'fixtures/history_unity_20261109/152632.png')
    locator=WorkshopLocator();normalized=locator.normalize(image,'reference')
    assert locator.verified
    reading=ItemIdentityReader(artwork_only=True).read(normalized,lambda _:pytest.fail('History/name OCR forbidden'),[])
    assert reading.known=='Anneau de Padgref'
