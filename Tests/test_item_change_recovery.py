from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image
from forgely import GameCapture,GameNotForeground,Forgely
from forgely_jet import parse_jet
from forgely_equipment_catalog import EquipmentCatalog
import pytest


def test_native_nonworkshop_pixels_never_reach_item_identification():
    cap=GameCapture()
    window=SimpleNamespace(_hWnd=42,title='DOFUS',width=1648,height=928,isMinimized=False)
    with patch('forgely.foreground_handle',return_value=99), patch('forgely.list_dofus_windows',return_value=[window]), patch('forgely.foreground_belongs_to_game',return_value=False), patch.object(cap,'_native_image',return_value=Image.new('RGB',(1648,928),'white')):
        with pytest.raises(GameNotForeground):cap.capture()


def test_gelano_zero_pa_ocr_is_explicit_even_when_zero_looks_like_o():
    assert parse_jet('1 1 # OPA')=={'PA':0}
    assert parse_jet('1 1 O PA')=={'PA':0}
    assert parse_jet('OPA')=={}
    assert parse_jet('1 1 # OPM')=={'PM':0}
    assert parse_jet('1 1 PA')=={'PA':1}


def test_reselecting_equipment_resumes_an_already_running_observer():
    item=EquipmentCatalog().get(14092)
    app=Mock();app.running=True
    app.toggle_observer.side_effect=lambda:setattr(app,'running',False)
    with patch('forgely.save_plan',return_value={'item':item.identity_name,'stats':{'Force':{'target':40}}}),patch('forgely.register_item'):
        Forgely.commit_equipment_selection(app,item,{'Force':(None,40)})
    app.toggle_observer.assert_called_once()
    app.after.assert_called_once_with(0,app.toggle_observer)
    assert not app.manual_equipment.invalidated
    assert app.manual_equipment.reference_icon is None
    assert app.current_slot_status==app.manual_equipment.reason


def test_focus_switch_during_desktop_capture_discards_the_frame():
    cap=GameCapture()
    window=SimpleNamespace(_hWnd=42,title='DOFUS',width=1648,height=928,isMinimized=False)
    with patch('forgely.foreground_handle',side_effect=[42,99]),patch('forgely.list_dofus_windows',return_value=[window]),patch('forgely.foreground_belongs_to_game',side_effect=lambda active,hwnd:active==hwnd),patch.object(cap,'_foreground_image',return_value=Image.new('RGB',(1648,928),'white')):
        with pytest.raises(GameNotForeground):cap.capture()
